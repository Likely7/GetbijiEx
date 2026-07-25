#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { constants as fsConstants, realpathSync } from "node:fs";
import { access, mkdir, readFile, rename, stat, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const CONFIG_VERSION = 1;
const CONFIG_FILE_NAME = "cli_runtime.json";

class LauncherError extends Error {
  constructor(kind, message) {
    super(message);
    this.name = kind;
    this.kind = kind;
  }
}

export function appDataRoot({
  platform = process.platform,
  env = process.env,
  home = os.homedir(),
} = {}) {
  if (env.GETBIJIEX_DATA_DIR) {
    return path.resolve(env.GETBIJIEX_DATA_DIR);
  }
  if (platform === "darwin") {
    return path.join(home, "Library", "Application Support", "GetbijiEx");
  }
  if (platform === "win32") {
    return path.join(env.APPDATA || path.join(home, "AppData", "Roaming"), "GetbijiEx");
  }
  return path.join(home, ".local", "share", "GetbijiEx");
}

export function runtimeConfigPath(options = {}) {
  return path.join(appDataRoot(options), "config", CONFIG_FILE_NAME);
}

async function isFile(filePath) {
  try {
    return (await stat(filePath)).isFile();
  } catch {
    return false;
  }
}

async function isDirectory(directoryPath) {
  try {
    return (await stat(directoryPath)).isDirectory();
  } catch {
    return false;
  }
}

async function isRunnableFile(filePath, platform = process.platform) {
  if (!(await isFile(filePath))) {
    return false;
  }
  if (platform === "win32") {
    return true;
  }
  try {
    await access(filePath, fsConstants.X_OK);
    return true;
  } catch {
    return false;
  }
}

export async function normalizeExecutablePath(input, platform = process.platform) {
  const candidate = path.resolve(input);
  if (platform === "darwin" && candidate.toLowerCase().endsWith(".app")) {
    return path.join(candidate, "Contents", "MacOS", "GetbijiEx");
  }
  if (platform === "win32" && (await isDirectory(candidate))) {
    return path.join(candidate, "GetbijiEx.exe");
  }
  return candidate;
}

export function sourceDescriptor(root) {
  const resolvedRoot = path.resolve(root);
  return {
    type: "source",
    path: resolvedRoot,
    command: "uv",
    argsPrefix: [
      "--directory",
      resolvedRoot,
      "run",
      "python",
      "scripts/biji_cli.py",
    ],
    cwd: resolvedRoot,
  };
}

export function executableDescriptor(executablePath) {
  const resolvedPath = path.resolve(executablePath);
  return {
    type: "executable",
    path: resolvedPath,
    command: resolvedPath,
    argsPrefix: [],
    cwd: path.dirname(resolvedPath),
  };
}

async function validateSource(root) {
  return isFile(path.join(root, "scripts", "biji_cli.py"));
}

async function validateDescriptor(descriptor, platform = process.platform) {
  if (descriptor.type === "source") {
    return validateSource(descriptor.path);
  }
  if (descriptor.type === "executable") {
    return isRunnableFile(descriptor.path, platform);
  }
  return false;
}

async function descriptorFromExecutable(input, platform = process.platform) {
  return executableDescriptor(await normalizeExecutablePath(input, platform));
}

function descriptorFromConfig(config) {
  if (!config || config.version !== CONFIG_VERSION || typeof config.path !== "string") {
    throw new LauncherError("GetbijiExConfigInvalid", "保存的 GetbijiEx CLI 配置格式无效，请重新配置。");
  }
  if (config.type === "source") {
    return sourceDescriptor(config.path);
  }
  if (config.type === "executable") {
    return executableDescriptor(config.path);
  }
  throw new LauncherError("GetbijiExConfigInvalid", "保存的 GetbijiEx CLI 类型无效，请重新配置。");
}

async function readRuntimeConfig(configPath) {
  try {
    return JSON.parse(await readFile(configPath, "utf8"));
  } catch (error) {
    if (error?.code === "ENOENT") {
      return null;
    }
    if (error instanceof SyntaxError) {
      throw new LauncherError("GetbijiExConfigInvalid", `配置文件不是有效 JSON：${configPath}`);
    }
    throw error;
  }
}

function pathExecutableCandidates({ platform, env }) {
  const pathValue = env.PATH || env.Path || env.path || "";
  const names = platform === "win32"
    ? ["GetbijiEx.exe", "getbijiex.exe"]
    : ["GetbijiEx", "getbijiex"];
  return pathValue
    .split(path.delimiter)
    .filter(Boolean)
    .flatMap((directory) => names.map((name) => path.join(directory, name)));
}

function standardExecutableCandidates({ platform, env, home }) {
  if (platform === "darwin") {
    return [
      "/Applications/GetbijiEx.app/Contents/MacOS/GetbijiEx",
      path.join(home, "Applications", "GetbijiEx.app", "Contents", "MacOS", "GetbijiEx"),
    ];
  }
  if (platform === "win32") {
    return [
      env.LOCALAPPDATA && path.join(env.LOCALAPPDATA, "GetbijiEx", "GetbijiEx.exe"),
      env.LOCALAPPDATA && path.join(env.LOCALAPPDATA, "Programs", "GetbijiEx", "GetbijiEx.exe"),
      env.ProgramFiles && path.join(env.ProgramFiles, "GetbijiEx", "GetbijiEx.exe"),
      env["ProgramFiles(x86)"] && path.join(env["ProgramFiles(x86)"], "GetbijiEx", "GetbijiEx.exe"),
    ].filter(Boolean);
  }
  return [
    path.join(home, ".local", "bin", "GetbijiEx"),
    "/opt/GetbijiEx/GetbijiEx",
  ];
}

async function firstValidExecutable(candidates, platform) {
  for (const candidate of candidates) {
    if (await isRunnableFile(candidate, platform)) {
      return executableDescriptor(candidate);
    }
  }
  return null;
}

export async function resolveRuntime({
  platform = process.platform,
  env = process.env,
  home = os.homedir(),
  configPath = runtimeConfigPath({ platform, env, home }),
} = {}) {
  if (env.GETBIJIEX_EXECUTABLE) {
    const descriptor = await descriptorFromExecutable(env.GETBIJIEX_EXECUTABLE, platform);
    if (!(await validateDescriptor(descriptor, platform))) {
      throw new LauncherError(
        "GetbijiExPathInvalid",
        `GETBIJIEX_EXECUTABLE 指向的程序不存在或不可执行：${descriptor.path}`,
      );
    }
    return descriptor;
  }

  if (env.GETBIJIEX_SOURCE) {
    const descriptor = sourceDescriptor(env.GETBIJIEX_SOURCE);
    if (!(await validateDescriptor(descriptor, platform))) {
      throw new LauncherError(
        "GetbijiExPathInvalid",
        `GETBIJIEX_SOURCE 不是有效源码目录：${descriptor.path}`,
      );
    }
    return descriptor;
  }

  const savedConfig = await readRuntimeConfig(configPath);
  if (savedConfig) {
    const descriptor = descriptorFromConfig(savedConfig);
    if (!(await validateDescriptor(descriptor, platform))) {
      throw new LauncherError(
        "GetbijiExConfigStale",
        `保存的 GetbijiEx 路径已经失效：${descriptor.path}。请重新运行 configure。`,
      );
    }
    return descriptor;
  }

  const executable = await firstValidExecutable(
    [
      ...standardExecutableCandidates({ platform, env, home }),
      ...pathExecutableCandidates({ platform, env }),
    ],
    platform,
  );
  if (executable) {
    return executable;
  }

  throw new LauncherError(
    "GetbijiExNotFound",
    "没有找到 GetbijiEx。请在本机找到 GetbijiEx.app、GetbijiEx.exe 或源码目录，然后运行 configure --executable <路径> 或 configure --source <目录>。",
  );
}

export async function configureRuntime(args, options = {}) {
  let type = null;
  let rawPath = null;
  for (let index = 0; index < args.length; index += 1) {
    const argument = args[index];
    if (argument !== "--executable" && argument !== "--source") {
      throw new LauncherError("GetbijiExConfigureError", `不支持的 configure 参数：${argument}`);
    }
    if (type !== null) {
      throw new LauncherError("GetbijiExConfigureError", "--executable 和 --source 只能选择一个。");
    }
    type = argument === "--source" ? "source" : "executable";
    rawPath = args[index + 1];
    if (!rawPath) {
      throw new LauncherError("GetbijiExConfigureError", `${argument} 后面必须提供路径。`);
    }
    index += 1;
  }
  if (!type) {
    throw new LauncherError(
      "GetbijiExConfigureError",
      "请使用 configure --executable <路径> 或 configure --source <目录>。",
    );
  }

  const platform = options.platform || process.platform;
  const descriptor = type === "source"
    ? sourceDescriptor(rawPath)
    : await descriptorFromExecutable(rawPath, platform);
  if (!(await validateDescriptor(descriptor, platform))) {
    throw new LauncherError(
      "GetbijiExPathInvalid",
      type === "source"
        ? `不是有效的 GetbijiEx 源码目录：${descriptor.path}`
        : `GetbijiEx 程序不存在或不可执行：${descriptor.path}`,
    );
  }

  const configPath = options.configPath || runtimeConfigPath(options);
  await mkdir(path.dirname(configPath), { recursive: true });
  const config = { version: CONFIG_VERSION, type, path: descriptor.path };
  const temporaryPath = `${configPath}.${process.pid}.tmp`;
  await writeFile(temporaryPath, `${JSON.stringify(config, null, 2)}\n`, "utf8");
  await rename(temporaryPath, configPath);
  return { ...config, config_path: configPath };
}

export function runRuntime(descriptor, args) {
  const result = spawnSync(
    descriptor.command,
    [...descriptor.argsPrefix, ...args],
    {
      cwd: descriptor.cwd,
      stdio: "inherit",
      shell: false,
    },
  );
  if (result.error) {
    if (descriptor.type === "source" && result.error.code === "ENOENT") {
      throw new LauncherError(
        "GetbijiExDependencyMissing",
        "源码模式需要 uv。请先安装 uv，并确认 uv 已加入 PATH。",
      );
    }
    throw new LauncherError(
      "GetbijiExLaunchError",
      `无法启动 GetbijiEx：${result.error.message}`,
    );
  }
  if (result.signal) {
    return 1;
  }
  return result.status ?? 1;
}

function outputError(error) {
  const kind = error instanceof LauncherError ? error.kind : error?.name || "Error";
  const message = error?.message || String(error);
  process.stdout.write(`${JSON.stringify({ error: `${kind}: ${message}` })}\n`);
}

export async function main(args = process.argv.slice(2)) {
  try {
    if (args[0] === "configure") {
      const result = await configureRuntime(args.slice(1));
      process.stdout.write(`${JSON.stringify({ ok: true, ...result })}\n`);
      return 0;
    }
    const runtime = await resolveRuntime();
    return runRuntime(runtime, args);
  } catch (error) {
    outputError(error);
    return 1;
  }
}

function comparablePath(filePath) {
  try {
    return realpathSync(filePath);
  } catch {
    return path.resolve(filePath);
  }
}

const isDirectRun = process.argv[1]
  && comparablePath(process.argv[1]) === comparablePath(fileURLToPath(import.meta.url));
if (isDirectRun) {
  process.exitCode = await main();
}
