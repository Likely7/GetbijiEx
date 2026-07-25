import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { chmod, mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  appDataRoot,
  configureRuntime,
  normalizeExecutablePath,
  resolveRuntime,
  runRuntime,
  runtimeConfigPath,
  sourceDescriptor,
} from "../skills/getbijiex/scripts/getbijiex-cli.mjs";

async function temporaryDirectory(prefix) {
  return mkdtemp(path.join(os.tmpdir(), prefix));
}

async function createSource(root) {
  const scripts = path.join(root, "scripts");
  await mkdir(scripts, { recursive: true });
  await writeFile(path.join(scripts, "biji_cli.py"), "# test\n", "utf8");
}

async function createExecutable(filePath) {
  await mkdir(path.dirname(filePath), { recursive: true });
  await writeFile(filePath, "#!/bin/sh\nexit 0\n", "utf8");
  await chmod(filePath, 0o755);
}

test("appDataRoot follows platform conventions", () => {
  assert.equal(
    appDataRoot({ platform: "darwin", env: {}, home: "/Users/test" }),
    path.join("/Users/test", "Library", "Application Support", "GetbijiEx"),
  );
  assert.equal(
    appDataRoot({ platform: "win32", env: { APPDATA: "C:\\Data" }, home: "C:\\Users\\test" }),
    path.join("C:\\Data", "GetbijiEx"),
  );
  assert.equal(
    appDataRoot({ platform: "linux", env: {}, home: "/home/test" }),
    path.join("/home/test", ".local", "share", "GetbijiEx"),
  );
});

test("runtimeConfigPath supports isolated data directories", () => {
  assert.equal(
    runtimeConfigPath({ env: { GETBIJIEX_DATA_DIR: "/tmp/custom data" } }),
    path.join(path.resolve("/tmp/custom data"), "config", "cli_runtime.json"),
  );
});

test("normalizeExecutablePath accepts macOS app bundles", async () => {
  const app = path.resolve("Applications", "GetbijiEx.app");
  assert.equal(
    await normalizeExecutablePath(app, "darwin"),
    path.join(app, "Contents", "MacOS", "GetbijiEx"),
  );
});

test("environment source overrides saved configuration", async () => {
  const root = await temporaryDirectory("getbijiex-node-中文-");
  const source = path.join(root, "源码 path");
  await createSource(source);
  const configPath = path.join(root, "config.json");
  await writeFile(
    configPath,
    JSON.stringify({ version: 1, type: "source", path: "/missing" }),
    "utf8",
  );

  const runtime = await resolveRuntime({
    platform: "linux",
    env: { GETBIJIEX_SOURCE: source, PATH: "" },
    home: root,
    cwd: root,
    configPath,
  });

  assert.deepEqual(runtime, sourceDescriptor(source));
  assert.deepEqual(runtime.argsPrefix.slice(0, 3), ["--directory", source, "run"]);
});

test("configure persists and resolveRuntime reads a source path", async () => {
  const root = await temporaryDirectory("getbijiex-config-");
  const source = path.join(root, "Source With Spaces");
  const configPath = path.join(root, "settings", "cli_runtime.json");
  await createSource(source);

  const configured = await configureRuntime(["--source", source], {
    platform: "linux",
    configPath,
  });
  const saved = JSON.parse(await readFile(configPath, "utf8"));
  const runtime = await resolveRuntime({
    platform: "linux",
    env: { PATH: "" },
    home: root,
    cwd: root,
    configPath,
  });

  assert.equal(configured.type, "source");
  assert.deepEqual(saved, { version: 1, type: "source", path: path.resolve(source) });
  assert.equal(runtime.path, path.resolve(source));
});

test("configure accepts a macOS app and stores its inner executable", async () => {
  const root = await temporaryDirectory("getbijiex-app-");
  const app = path.join(root, "GetbijiEx App.app");
  const executable = path.join(app, "Contents", "MacOS", "GetbijiEx");
  const configPath = path.join(root, "config.json");
  await createExecutable(executable);

  const configured = await configureRuntime(["--executable", app], {
    platform: "darwin",
    configPath,
  });

  assert.equal(configured.path, executable);
});

test("resolveRuntime does not trust source files in the working directory", async () => {
  const root = await temporaryDirectory("getbijiex-untrusted-");
  const nested = path.join(root, "one", "two");
  await createSource(root);
  await mkdir(nested, { recursive: true });

  await assert.rejects(
    resolveRuntime({
      platform: "linux",
      env: { PATH: "" },
      home: path.join(root, "home"),
      cwd: nested,
      configPath: path.join(root, "missing.json"),
    }),
    { name: "GetbijiExNotFound" },
  );
});

test("resolveRuntime reports stale saved paths instead of silently falling back", async () => {
  const root = await temporaryDirectory("getbijiex-stale-");
  const configPath = path.join(root, "config.json");
  await writeFile(
    configPath,
    JSON.stringify({ version: 1, type: "source", path: path.join(root, "gone") }),
    "utf8",
  );

  await assert.rejects(
    resolveRuntime({
      platform: "linux",
      env: { PATH: "" },
      home: root,
      cwd: root,
      configPath,
    }),
    { name: "GetbijiExConfigStale" },
  );
});

test("resolveRuntime returns a clear not-found error", async () => {
  const root = await temporaryDirectory("getbijiex-missing-");

  await assert.rejects(
    resolveRuntime({
      platform: "linux",
      env: { PATH: "" },
      home: root,
      cwd: root,
      configPath: path.join(root, "missing.json"),
    }),
    { name: "GetbijiExNotFound" },
  );
});

test("source runtime reports a clear error when uv is unavailable", async () => {
  const root = await temporaryDirectory("getbijiex-no-uv-");
  const source = path.join(root, "source");
  await createSource(source);
  const descriptor = {
    ...sourceDescriptor(source),
    command: path.join(root, "missing-uv"),
  };

  assert.throws(
    () => runRuntime(descriptor, ["--help"]),
    { name: "GetbijiExDependencyMissing" },
  );
});

test("source runtime turns a failed dependency preflight into a structured error", async () => {
  const root = await temporaryDirectory("getbijiex-bad-python-");
  const source = path.join(root, "source");
  await createSource(source);
  const descriptor = {
    ...sourceDescriptor(source),
    command: path.join(root, "missing-runtime"),
  };

  assert.throws(
    () => runRuntime(descriptor, ["topics"]),
    (error) => error.name === "GetbijiExDependencyMissing"
      && error.message.includes("Python 3.11+"),
  );
});

test("launcher forwards arguments, output, and exit status", async () => {
  const root = await temporaryDirectory("getbijiex-forward-");
  const executable = process.execPath;
  const fakeCli = path.join(root, "fake-getbijiex.mjs");
  await writeFile(
    fakeCli,
    "const args = process.argv.slice(2).join(' ');\n"
      + "process.stdout.write(`stdout:${args}\\n`);\n"
      + "process.stderr.write(`stderr:${args}\\n`);\n"
      + "process.exitCode = 7;\n",
    "utf8",
  );
  const launcher = path.resolve("skills/getbijiex/scripts/getbijiex-cli.mjs");

  const result = spawnSync(
    process.execPath,
    [launcher, fakeCli, "export", "--name", "博主 名称"],
    {
      encoding: "utf8",
      env: {
        ...process.env,
        GETBIJIEX_EXECUTABLE: executable,
        GETBIJIEX_DATA_DIR: path.join(root, "data"),
      },
    },
  );

  assert.equal(result.status, 7);
  assert.match(result.stdout, /stdout:export --name 博主 名称/);
  assert.match(result.stderr, /stderr:export --name 博主 名称/);
});

test("launcher runs when invoked from a copied installation path", async () => {
  const root = await temporaryDirectory("getbijiex-copy-");
  const executable = process.execPath;
  const fakeCli = path.join(root, "fake-getbijiex.mjs");
  const installedDirectory = path.join(root, "installed");
  await writeFile(
    fakeCli,
    "process.stdout.write(`copied:${process.argv.slice(2).join(' ')}\\n`);\n",
    "utf8",
  );
  await mkdir(installedDirectory, { recursive: true });
  const launcher = path.resolve("skills/getbijiex/scripts/getbijiex-cli.mjs");
  const installedLauncher = path.join(installedDirectory, "getbijiex-cli.mjs");
  await writeFile(installedLauncher, await readFile(launcher));

  const result = spawnSync(process.execPath, [installedLauncher, fakeCli, "--help"], {
    encoding: "utf8",
    env: {
      ...process.env,
      GETBIJIEX_LAUNCHER_LIBRARY: "0",
      GETBIJIEX_EXECUTABLE: executable,
      GETBIJIEX_DATA_DIR: path.join(root, "data"),
    },
  });

  assert.equal(result.status, 0);
  assert.match(result.stdout, /copied:--help/);
});

test("launcher prints JSON when no runtime can be found", async () => {
  const root = await temporaryDirectory("getbijiex-json-error-");
  const launcher = path.resolve("skills/getbijiex/scripts/getbijiex-cli.mjs");
  const result = spawnSync(process.execPath, [launcher, "topics"], {
    cwd: root,
    encoding: "utf8",
    env: {
      GETBIJIEX_LAUNCHER_LIBRARY: "0",
      GETBIJIEX_DATA_DIR: path.join(root, "data"),
      HOME: root,
      PATH: "",
    },
  });

  assert.equal(result.status, 1);
  assert.match(JSON.parse(result.stdout).error, /^GetbijiExNotFound:/);
  assert.equal(result.stderr, "");
});
