from pathlib import Path
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import auto_token
from scripts import biji_export
from scripts import skill_installer
from scripts.app_paths import output_dir, user_data_root


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GetbijiEx")
        self.root.geometry("760x960")

        self.url_var = tk.StringVar()
        self.topic_id_var = tk.StringVar()
        self.status_var = tk.StringVar(value="准备就绪")
        self.output_dir_var = tk.StringVar(value=str(output_dir()))
        self.authorization_var = tk.StringVar()
        self.csrf_var = tk.StringVar()
        self.appid_var = tk.StringVar(value="3")
        self.topics = []
        self.follows = []
        self._ui_queue = queue.Queue()
        self._retry_after_token = None  # Token 刷新后要重试的动作
        self._token_auto_retried = False  # 防止过期→刷新→重试死循环

        self.build_ui()
        self.refresh_auth_status()
        self.root.after(100, self._poll_ui_queue)

    def _poll_ui_queue(self):
        """主线程轮询工作线程发来的回调（macOS 上从子线程直接调 root.after 不会唤醒 mainloop）"""
        while True:
            try:
                callback, args = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            callback(*args)
        self.root.after(100, self._poll_ui_queue)

    def _call_ui(self, callback, *args):
        """工作线程安全地调度 UI 操作"""
        self._ui_queue.put((callback, args))

    def build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text="GetbijiEx", font=("Arial", 18, "bold"))
        title.pack(anchor="w")

        desc = ttk.Label(
            main,
            text="选择知识库和博主，一键导出 Markdown / JSON。",
        )
        desc.pack(anchor="w", pady=(4, 16))

        auth_frame = ttk.LabelFrame(main, text="1. 登录状态 / Token", padding=12)
        auth_frame.pack(fill="x")

        self.auth_label = ttk.Label(auth_frame, text="未检测")
        self.auth_label.pack(anchor="w")

        ttk.Label(
            auth_frame,
            text="点“自动获取 Token”后会弹出 Chrome：首次使用请登录 biji，登录成功后自动完成；以后点一下即可。抓不到时再手动粘贴。",
            wraplength=680,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        auth_btns = ttk.Frame(auth_frame)
        auth_btns.pack(anchor="w", pady=(10, 0))

        self.open_login_button = ttk.Button(auth_btns, text="自动获取 Token", command=self.handle_auto_token)
        self.open_login_button.pack(side="left")

        self.save_token_button = ttk.Button(auth_btns, text="保存 Token", command=self.handle_save_token)
        self.save_token_button.pack(side="left", padx=(8, 0))

        ttk.Button(auth_btns, text="刷新状态", command=self.refresh_auth_status).pack(side="left", padx=(8, 0))

        token_form = ttk.Frame(auth_frame)
        token_form.pack(fill="x", pady=(12, 0))
        token_form.columnconfigure(1, weight=1)

        ttk.Label(token_form, text="authorization").grid(row=0, column=0, sticky="w")
        ttk.Entry(token_form, textvariable=self.authorization_var).grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 8))

        ttk.Label(token_form, text="xi-csrf-token").grid(row=1, column=0, sticky="w")
        ttk.Entry(token_form, textvariable=self.csrf_var).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(0, 8))

        ttk.Label(token_form, text="x-appid").grid(row=2, column=0, sticky="w")
        ttk.Entry(token_form, textvariable=self.appid_var, width=16).grid(row=2, column=1, sticky="w", padx=(10, 0))

        agent_frame = ttk.LabelFrame(main, text="Agent 集成（可选）", padding=12)
        agent_frame.pack(fill="x", pady=(16, 0))

        agent_row = ttk.Frame(agent_frame)
        agent_row.pack(fill="x")
        ttk.Button(
            agent_row,
            text="安装 Skill 到 Claude Code",
            command=lambda: self.handle_install_skill("claude"),
        ).pack(side="left")
        ttk.Button(
            agent_row,
            text="安装到 Codex",
            command=lambda: self.handle_install_skill("codex"),
        ).pack(side="left", padx=(8, 0))
        ttk.Label(
            agent_frame,
            text="安装后 Agent 可直接调用 GetbijiEx 导出笔记，不用打开本软件；其他 Agent 可使用命令行自定义安装目录。",
            wraplength=680,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        export_frame = ttk.LabelFrame(main, text="2. 导出笔记", padding=12)
        export_frame.pack(fill="x", pady=(16, 0))

        self.load_topics_button = ttk.Button(export_frame, text="加载知识库", command=self.handle_load_topics)
        self.load_topics_button.grid(row=0, column=0, sticky="w")
        self.topic_combo = ttk.Combobox(export_frame, state="readonly", width=60)
        self.topic_combo.grid(row=0, column=1, sticky="ew", padx=(12, 0))
        self.topic_combo.bind("<<ComboboxSelected>>", self.handle_topic_selected)

        ttk.Label(export_frame, text="博主").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.follow_combo = ttk.Combobox(export_frame, state="readonly", width=60)
        self.follow_combo.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(10, 0))

        self.export_button = ttk.Button(export_frame, text="开始导出", command=self.handle_export)
        self.export_button.grid(row=2, column=1, sticky="w", pady=(12, 0))

        self.progress = ttk.Progressbar(export_frame, mode="indeterminate")
        self.progress.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        ttk.Separator(export_frame, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 8))
        ttk.Label(export_frame, text="手动模式（可选）：粘贴 Biji 博主 URL").grid(row=5, column=0, columnspan=2, sticky="w")
        ttk.Entry(export_frame, textvariable=self.url_var, width=88).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(4, 6))
        ttk.Label(export_frame, text="Topic ID（可选）").grid(row=7, column=0, sticky="w")
        ttk.Entry(export_frame, textvariable=self.topic_id_var, width=24).grid(row=7, column=1, sticky="w", padx=(12, 0))

        export_frame.columnconfigure(1, weight=1)

        output_frame = ttk.LabelFrame(main, text="3. 输出目录", padding=12)
        output_frame.pack(fill="x", pady=(16, 0))

        ttk.Label(output_frame, text=f"应用数据目录：{user_data_root()}").pack(anchor="w", pady=(0, 6))
        ttk.Label(output_frame, textvariable=self.output_dir_var).pack(anchor="w")

        output_buttons = ttk.Frame(output_frame)
        output_buttons.pack(anchor="w", pady=(10, 0))
        ttk.Button(
            output_buttons,
            text="选择输出目录",
            command=self.choose_output_dir,
        ).pack(side="left")
        ttk.Button(
            output_buttons,
            text="恢复默认目录",
            command=self.reset_output_dir,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            output_buttons,
            text="打开输出目录",
            command=self.open_output_dir,
        ).pack(side="left", padx=(8, 0))

        log_frame = ttk.LabelFrame(main, text="运行日志", padding=12)
        log_frame.pack(fill="both", expand=True, pady=(16, 0))

        self.log_text = tk.Text(log_frame, height=12, wrap="word")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

        status_bar = ttk.Label(main, textvariable=self.status_var)
        status_bar.pack(anchor="w", pady=(12, 0))

    def append_log(self, text: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def set_busy(self, busy: bool, status: str):
        state = "disabled" if busy else "normal"
        self.open_login_button.configure(state=state)
        self.save_token_button.configure(state=state)
        self.load_topics_button.configure(state=state)
        self.export_button.configure(state=state)
        self.status_var.set(status)

    def refresh_auth_status(self):
        self.authorization_var.set("")
        self.csrf_var.set("")
        self.appid_var.set("3")
        if biji_export.CONFIG_PATH.exists():
            try:
                data = biji_export.json.loads(biji_export.CONFIG_PATH.read_text(encoding="utf-8"))
                token = data.get("authorization", "")
                csrf = data.get("xi-csrf-token", "")
                appid = data.get("x-appid", "3")
                self.authorization_var.set(token)
                self.csrf_var.set(csrf)
                self.appid_var.set(appid or "3")
                if token:
                    masked = token[:18] + "..." if len(token) > 18 else token
                    self.auth_label.configure(text=f"已配置 Token：{masked}")
                    return
            except Exception:
                pass
        self.auth_label.configure(text="未检测到有效 Token，请先保存。")

    def handle_load_topics(self):
        self._token_auto_retried = False
        self.set_busy(True, "正在加载知识库...")
        self.append_log("正在加载知识库列表…")
        threading.Thread(target=self._load_topics_worker, daemon=True).start()

    def _load_topics_worker(self):
        try:
            topics = biji_export.list_topics()
        except Exception as exc:
            self._call_ui(self._load_topics_done, None, exc)
        else:
            self._call_ui(self._load_topics_done, topics, None)

    def _load_topics_done(self, topics, error):
        self.set_busy(False, "准备就绪")
        if error is not None:
            self._show_load_error("加载知识库失败", error, retry=self.handle_load_topics)
            return
        self.topics = topics
        self.follows = []
        self.follow_combo.set("")
        self.follow_combo.configure(values=[])
        self.topic_combo.configure(
            values=[f"{t['name']}（{t['count']} 个内容）" for t in topics]
        )
        self.append_log(f"✅ 已加载 {len(topics)} 个知识库")
        if topics:
            self.topic_combo.current(0)
            self.handle_topic_selected()

    def handle_topic_selected(self, event=None):
        index = self.topic_combo.current()
        if index < 0 or index >= len(self.topics):
            return
        topic = self.topics[index]
        self.set_busy(True, "正在加载博主列表...")
        self.append_log(f"正在加载「{topic['name']}」的博主列表…")
        threading.Thread(target=self._load_follows_worker, args=(topic,), daemon=True).start()

    def _load_follows_worker(self, topic):
        try:
            follows = biji_export.list_follows(topic["id_alias"])
        except Exception as exc:
            self._call_ui(self._load_follows_done, None, exc)
        else:
            self._call_ui(self._load_follows_done, follows, None)

    def _load_follows_done(self, follows, error):
        self.set_busy(False, "准备就绪")
        if error is not None:
            self._show_load_error("加载博主列表失败", error, retry=self.handle_topic_selected)
            return
        self.follows = follows
        self.follow_combo.configure(
            values=[f"{f['name']}（{f['note_count']} 篇）" for f in follows]
        )
        self.append_log(f"✅ 共 {len(follows)} 位博主")
        if follows:
            self.follow_combo.current(0)

    def _show_load_error(self, title, error, retry=None):
        if isinstance(error, biji_export.AuthError) and retry is not None and not self._token_auto_retried:
            # JWT 只有约 30 分钟有效期，过期是常态：自动重抓 Token 并重试一次
            self._token_auto_retried = True
            self._retry_after_token = retry
            self.append_log("Token 已过期，正在自动重新获取…")
            self.handle_auto_token()
            return
        if isinstance(error, biji_export.AuthError):
            self.append_log("❌ Token 已过期，请重新点「自动获取 Token」")
            messagebox.showerror(title, "Token 已过期，请重新点「自动获取 Token」")
        else:
            self.append_log(f"❌ {error}")
            messagebox.showerror(title, str(error))

    def handle_auto_token(self):
        self.set_busy(True, "正在自动获取 Token...")
        self.append_log("启动 Chrome，准备自动获取 Token…")
        threading.Thread(target=self._auto_token_worker, daemon=True).start()

    def _auto_token_worker(self):
        def log(msg):
            self._call_ui(self.append_log, msg)

        try:
            auto_token.capture_token(log=log)
        except auto_token.CaptureCancelled:
            self._call_ui(self._auto_token_done, None)
        except Exception as exc:
            self._call_ui(self._auto_token_done, str(exc))
        else:
            self._call_ui(self._auto_token_done, "success")

    def _auto_token_done(self, result):
        self.set_busy(False, "准备就绪")
        self.refresh_auth_status()
        if result == "success":
            self.append_log("✅ Token 已自动获取并保存")
            retry = self._retry_after_token
            self._retry_after_token = None
            if retry is not None:
                retry()
            else:
                self.handle_load_topics()
        elif result is None:
            self.append_log("已取消获取 Token（浏览器窗口被关闭）")
        else:
            self.append_log(f"❌ {result}")
            messagebox.showerror("获取失败", result)

    def handle_save_token(self):
        authorization = self.authorization_var.get().strip()
        csrf = self.csrf_var.get().strip()
        appid = self.appid_var.get().strip() or "3"

        if not authorization:
            messagebox.showwarning("缺少 Token", "请先粘贴 authorization")
            return
        if not csrf:
            messagebox.showwarning("缺少 Token", "请先粘贴 xi-csrf-token")
            return
        if not authorization.startswith("Bearer "):
            authorization = "Bearer " + authorization
            self.authorization_var.set(authorization)

        self.set_busy(True, "正在保存 Token...")
        try:
            biji_export.save_auth_config(
                {
                    "authorization": authorization,
                    "xi-csrf-token": csrf,
                    "x-appid": appid,
                }
            )
            self.append_log("✅ Token 已保存")
            self.refresh_auth_status()
            messagebox.showinfo("保存成功", f"Token 已保存到：\n{biji_export.CONFIG_PATH}")
        except Exception as exc:
            self.append_log(f"❌ {exc}")
            messagebox.showerror("保存失败", str(exc))
        finally:
            self.set_busy(False, "准备就绪")

    def handle_export(self):
        follow_index = self.follow_combo.current()
        topic_index = self.topic_combo.current()
        use_selection = (
            0 <= follow_index < len(self.follows)
            and 0 <= topic_index < len(self.topics)
        )

        topic_text = self.topic_id_var.get().strip()
        topic_id = None
        if topic_text:
            try:
                topic_id = int(topic_text)
            except ValueError:
                messagebox.showwarning("Topic ID 无效", "Topic ID 必须是数字")
                return

        url = None
        follow = None
        topic = None
        if use_selection:
            follow = self.follows[follow_index]
            topic = self.topics[topic_index]
            target_desc = f"{topic['name']} / {follow['name']}"
        else:
            url = self.url_var.get().strip()
            if not url:
                messagebox.showwarning("缺少导出目标", "请先选择知识库和博主，或粘贴 biji 博主页面 URL")
                return
            target_desc = url

        output = self.output_dir_var.get().strip() or None
        self.set_busy(True, "正在导出笔记...")
        self.progress.configure(mode="indeterminate", value=0)
        self.progress.start(15)
        self.append_log(f"开始导出：{target_desc}")
        threading.Thread(
            target=self._export_worker,
            args=(url, topic_id, output, follow, topic),
            daemon=True,
        ).start()

    def _export_worker(self, url, topic_id, output, follow=None, topic=None):
        def on_progress(current, total, title):
            self._call_ui(self._export_progress, current, total, title)

        try:
            if follow is not None:
                result = biji_export.export_notes_core(
                    follow["follow_id"],
                    follow["name"],
                    topic["id_alias"],
                    topic_id_override=topic_id if topic_id is not None else follow.get("topic_id"),
                    output_dir=output,
                    progress=on_progress,
                )
            else:
                result = biji_export.export_notes(
                    url, topic_id_override=topic_id, output_dir=output,
                    progress=on_progress,
                )
        except Exception as exc:
            self._call_ui(self._export_done, None, str(exc))
        else:
            self._call_ui(self._export_done, result, None)

    def _export_progress(self, current, total, title):
        if str(self.progress.cget("mode")) == "indeterminate":
            self.progress.stop()
            self.progress.configure(mode="determinate", maximum=total)
        self.progress.configure(value=current)
        short = title.replace("\n", " ")[:20]
        self.status_var.set(f"正在导出 {current}/{total}：{short}")

    def _export_done(self, result, error):
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.set_busy(False, "准备就绪")
        self.refresh_auth_status()
        if error is not None:
            self.append_log(f"❌ {error}")
            messagebox.showerror("操作失败", error)
            return
        self.append_log(f"✅ 导出完成：{result['author_name']}，共 {result['count']} 条")
        self.append_log(f"输出目录：{result['output_dir']}")
        self.append_log(f"Markdown：{result['markdown_path']}")
        self.append_log(f"JSON：{result['json_path']}")
        self.open_path(result["output_dir"])
        messagebox.showinfo("导出完成", f"已导出 {result['count']} 条笔记\n\n输出目录:\n{result['output_dir']}\n\nMarkdown:\n{result['markdown_path']}")

    def choose_output_dir(self):
        selected = filedialog.askdirectory(initialdir=self.output_dir_var.get() or str(output_dir()))
        if selected:
            self.output_dir_var.set(str(Path(selected).expanduser()))
            self.append_log(f"已切换输出目录：{self.output_dir_var.get()}")

    def reset_output_dir(self):
        default_dir = str(output_dir())
        self.output_dir_var.set(default_dir)
        self.append_log(f"已恢复默认输出目录：{default_dir}")

    def handle_install_skill(self, agent="claude"):
        agent_name = "Claude Code" if agent == "claude" else "Codex"
        try:
            target = skill_installer.install_skill(agent=agent)
            self.append_log(f"✅ {agent_name} Skill 已安装：{target}")
            messagebox.showinfo(
                "安装成功",
                f"Skill 已安装到：\n{target}\n\n之后可直接对 {agent_name} 说「导出 biji 博主笔记」。",
            )
        except Exception as exc:
            self.append_log(f"❌ {exc}")
            messagebox.showerror("安装失败", str(exc))

    def open_output_dir(self):
        self.open_path(self.output_dir_var.get())

    def open_path(self, path):
        """在系统文件管理器中打开目录（跨平台）"""
        path = Path(path).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            elif sys.platform.startswith("win"):
                os.startfile(str(path))
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception as exc:
            self.append_log(f"⚠️ 无法自动打开目录：{exc}")


def main():
    root = tk.Tk()
    style = ttk.Style(root)
    if "aqua" in style.theme_names():
        style.theme_use("aqua")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
