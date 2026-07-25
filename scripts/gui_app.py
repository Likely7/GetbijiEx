from pathlib import Path
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
from scripts.app_paths import output_dir, user_data_root


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Biji 导出小工具")
        self.root.geometry("760x760")

        self.url_var = tk.StringVar()
        self.topic_id_var = tk.StringVar()
        self.status_var = tk.StringVar(value="准备就绪")
        self.output_dir_var = tk.StringVar(value=str(output_dir()))
        self.authorization_var = tk.StringVar()
        self.csrf_var = tk.StringVar()
        self.appid_var = tk.StringVar(value="3")

        self.build_ui()
        self.refresh_auth_status()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text="Biji 导出小工具", font=("Arial", 18, "bold"))
        title.pack(anchor="w")

        desc = ttk.Label(
            main,
            text="输入博主页面 URL，一键保存 Token、导出 Markdown。",
        )
        desc.pack(anchor="w", pady=(4, 16))

        auth_frame = ttk.LabelFrame(main, text="1. 登录状态 / Token", padding=12)
        auth_frame.pack(fill="x")

        self.auth_label = ttk.Label(auth_frame, text="未检测")
        self.auth_label.pack(anchor="w")

        ttk.Label(
            auth_frame,
            text="点“自动获取 Token”后会弹出 Chrome：首次使用请登录 biji 并打开任意笔记，之后自动完成。抓不到时再手动粘贴。",
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

        export_frame = ttk.LabelFrame(main, text="2. 导出笔记", padding=12)
        export_frame.pack(fill="x", pady=(16, 0))

        ttk.Label(export_frame, text="Biji 博主 URL").grid(row=0, column=0, sticky="w")
        ttk.Entry(export_frame, textvariable=self.url_var, width=88).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 10))

        ttk.Label(export_frame, text="Topic ID（可选）").grid(row=2, column=0, sticky="w")
        ttk.Entry(export_frame, textvariable=self.topic_id_var, width=24).grid(row=3, column=0, sticky="w", pady=(4, 0))

        self.export_button = ttk.Button(export_frame, text="开始导出", command=self.handle_export)
        self.export_button.grid(row=3, column=1, sticky="w", padx=(12, 0))

        export_frame.columnconfigure(0, weight=1)

        output_frame = ttk.LabelFrame(main, text="3. 输出目录", padding=12)
        output_frame.pack(fill="x", pady=(16, 0))

        ttk.Label(output_frame, text=f"应用数据目录：{user_data_root()}").pack(anchor="w", pady=(0, 6))
        ttk.Label(output_frame, textvariable=self.output_dir_var).pack(anchor="w")
        ttk.Button(output_frame, text="选择输出目录", command=self.choose_output_dir).pack(anchor="w", pady=(10, 0))
        ttk.Button(output_frame, text="恢复默认目录", command=self.reset_output_dir).pack(anchor="w", pady=(8, 0))
        ttk.Button(output_frame, text="打开输出目录", command=self.open_output_dir).pack(anchor="w", pady=(8, 0))

        log_frame = ttk.LabelFrame(main, text="运行日志", padding=12)
        log_frame.pack(fill="both", expand=True, pady=(16, 0))

        self.log_text = tk.Text(log_frame, height=18, wrap="word")
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

    def handle_auto_token(self):
        self.set_busy(True, "正在自动获取 Token...")
        self.append_log("启动 Chrome，准备自动获取 Token…")
        threading.Thread(target=self._auto_token_worker, daemon=True).start()

    def _auto_token_worker(self):
        def log(msg):
            self.root.after(0, self.append_log, msg)

        try:
            auto_token.capture_token(log=log)
        except auto_token.CaptureCancelled:
            self.root.after(0, self._auto_token_done, None)
        except Exception as exc:
            self.root.after(0, self._auto_token_done, str(exc))
        else:
            self.root.after(0, self._auto_token_done, "success")

    def _auto_token_done(self, result):
        self.set_busy(False, "准备就绪")
        self.refresh_auth_status()
        if result == "success":
            self.append_log("✅ Token 已自动获取并保存")
            messagebox.showinfo("获取成功", "Token 已自动获取并保存")
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
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("缺少 URL", "请先输入 biji 博主页面 URL")
            return

        topic_text = self.topic_id_var.get().strip()
        topic_id = None
        if topic_text:
            try:
                topic_id = int(topic_text)
            except ValueError:
                messagebox.showwarning("Topic ID 无效", "Topic ID 必须是数字")
                return

        output = self.output_dir_var.get().strip() or None
        self.set_busy(True, "正在导出笔记...")
        self.append_log(f"开始导出：{url}")
        threading.Thread(
            target=self._export_worker, args=(url, topic_id, output), daemon=True
        ).start()

    def _export_worker(self, url, topic_id, output):
        try:
            result = biji_export.export_notes(
                url, topic_id_override=topic_id, output_dir=output
            )
        except Exception as exc:
            self.root.after(0, self._export_done, None, str(exc))
        else:
            self.root.after(0, self._export_done, result, None)

    def _export_done(self, result, error):
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

    def open_output_dir(self):
        path = Path(self.output_dir_var.get()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["open", str(path)], check=False)


def main():
    root = tk.Tk()
    style = ttk.Style(root)
    if "aqua" in style.theme_names():
        style.theme_use("aqua")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
