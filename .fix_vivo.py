#!/usr/bin/env python3

from pathlib import Path
import shutil
import re
import sys
import time

ROOT = Path.cwd()

MAIN = ROOT / "app/src/main/java/com/bintang/vivofastboot/MainActivity.java"
USB = ROOT / "app/src/main/java/com/bintang/vivofastboot/FastbootUsbTransport.java"

def log(msg):
    print("[VivoFix] " + str(msg))

def backup(path):
    if not path.exists():
        log("SKIP missing: " + str(path))
        return False

    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        log("Backup: " + str(bak))

    return True

def read(path):
    return path.read_text(encoding="utf-8")

def write(path, text):
    path.write_text(text, encoding="utf-8")
    log("Written: " + str(path))

def replace_once(text, old, new, name):
    if old not in text:
        log("NOT FOUND: " + name)
        return text, False

    text = text.replace(old, new, 1)
    log("PATCHED: " + name)
    return text, True

def contains_method(text, marker):
    return marker in text

def main():
    log("VivoFastboot patcher")
    log("Project: " + str(ROOT))

    if not MAIN.exists():
        log("MainActivity.java tidak ditemukan")
    if not USB.exists():
        log("FastbootUsbTransport.java tidak ditemukan")

    if MAIN.exists():
        backup(MAIN)

    if USB.exists():
        backup(USB)

if __name__ == "__main__":
    main()

def patch_usb_helpers():
    if not USB.exists():
        return

    text = read(USB)

    if "VIVO_FASTBOOT_PATCH_HELPERS" in text:
        log("USB helpers sudah ada")
        return

    helper = r'''
    /* VIVO_FASTBOOT_PATCH_HELPERS */

    public String normalizeFastbootResponse(String response) {
        if (response == null) {
            return "";
        }

        return response
                .replace("\r", "")
                .replace("\u0000", "")
                .trim();
    }

    public boolean fastbootSuccess(String response) {
        String r = normalizeFastbootResponse(response).toLowerCase();

        return r.contains("ok")
                || r.contains("okay")
                || r.contains("finished")
                || r.contains("success");
    }

    public boolean fastbootFailure(String response) {
        String r = normalizeFastbootResponse(response).toLowerCase();

        return r.contains("fail")
                || r.contains("error")
                || r.contains("unknown command")
                || r.contains("not found")
                || r.contains("denied");
    }

    public String explainFastbootResponse(String response) {
        String r = normalizeFastbootResponse(response);

        if (r.length() == 0) {
            return "Tidak ada response dari bootloader.";
        }

        if (fastbootFailure(r)) {
            return "Bootloader menolak command: " + r;
        }

        return r;
    }

'''

    # Insert before the final class closing brace.
    pos = text.rfind("}")
    if pos < 0:
        log("USB class closing brace tidak ditemukan")
        return

    text = text[:pos] + helper + text[pos:]
    write(USB, text)

patch_usb_helpers()

def patch_vivo_unlock_helpers():
    if not USB.exists():
        return

    text = read(USB)

    if "VIVO_UNLOCK_COMMANDS" in text:
        log("Vivo unlock helper sudah ada")
        return

    helper = r'''
    /* VIVO_UNLOCK_COMMANDS */

    public String[] getVivoUnlockCommands(String protocol) {
        String p = protocol == null ? "" : protocol.toLowerCase();

        if (p.contains("old") || p.contains("bbk")) {
            return new String[] {
                    "bbk unlock_vivo"
            };
        }

        if (p.contains("vivo_bsp")) {
            return new String[] {
                    "vivo_bsp unlock_vivo"
            };
        }

        return new String[] {
                "vivo_bsp unlock_vivo",
                "bbk unlock_vivo"
        };
    }

    public String[] getVivoLockCommands(String protocol) {
        String p = protocol == null ? "" : protocol.toLowerCase();

        if (p.contains("old") || p.contains("bbk")) {
            return new String[] {
                    "bbk lock_vivo"
            };
        }

        if (p.contains("vivo_bsp")) {
            return new String[] {
                    "vivo_bsp lock_vivo"
            };
        }

        return new String[] {
                "vivo_bsp lock_vivo",
                "bbk lock_vivo"
        };
    }

'''

    pos = text.rfind("}")
    if pos < 0:
        log("USB class closing brace tidak ditemukan")
        return

    text = text[:pos] + helper + text[pos:]
    write(USB, text)

patch_vivo_unlock_helpers()

def patch_main_crash_handler():
    if not MAIN.exists():
        return

    text = read(MAIN)

    if "VIVO_CRASH_HANDLER" in text:
        log("Crash handler sudah ada")
        return

    helper = r'''
    /* VIVO_CRASH_HANDLER */

    private void installVivoCrashHandler() {
        final Thread.UncaughtExceptionHandler previous =
                Thread.getDefaultUncaughtExceptionHandler();

        Thread.setDefaultUncaughtExceptionHandler(
                new Thread.UncaughtExceptionHandler() {
                    @Override
                    public void uncaughtException(
                            Thread thread,
                            Throwable throwable) {

                        try {
                            StringBuilder out = new StringBuilder();

                            out.append("=== VivoFastboot Crash ===\n");
                            out.append("Thread: ")
                               .append(thread != null ? thread.getName() : "unknown")
                               .append("\n\n");

                            out.append("Exception: ")
                               .append(throwable.getClass().getName())
                               .append("\n");

                            if (throwable.getMessage() != null) {
                                out.append("Message: ")
                                   .append(throwable.getMessage())
                                   .append("\n");
                            }

                            out.append("\nStack trace:\n");

                            for (StackTraceElement e : throwable.getStackTrace()) {
                                out.append("at ")
                                   .append(e.toString())
                                   .append("\n");
                            }

                            appendVivoOutput(out.toString());

                        } catch (Throwable ignored) {
                            // Jangan biarkan crash handler menyebabkan crash kedua.
                        }

                        /*
                         * Jangan force-close aplikasi dari sini.
                         * Android tetap mengatur lifecycle setelah uncaught exception.
                         */
                    }
                }
        );
    }

    private void appendVivoOutput(String message) {
        try {
            /*
             * Cari TextView output secara dinamis supaya helper ini
             * tidak bergantung pada nama ID tertentu.
             */
            android.view.View root = findViewById(android.R.id.content);

            if (root == null) {
                return;
            }

            android.widget.TextView output = findOutputTextView(root);

            if (output != null) {
                String old = output.getText() == null
                        ? ""
                        : output.getText().toString();

                output.setText(old + "\n\n" + message);
            }
        } catch (Throwable ignored) {
        }
    }

    private android.widget.TextView findOutputTextView(android.view.View view) {
        if (view instanceof android.widget.TextView) {
            return (android.widget.TextView) view;
        }

        if (view instanceof android.view.ViewGroup) {
            android.view.ViewGroup group = (android.view.ViewGroup) view;

            for (int i = 0; i < group.getChildCount(); i++) {
                android.widget.TextView found =
                        findOutputTextView(group.getChildAt(i));

                if (found != null) {
                    String idName = "";

                    try {
                        int id = found.getId();

                        if (id != android.view.View.NO_ID) {
                            idName = getResources()
                                    .getResourceEntryName(id)
                                    .toLowerCase();
                        }
                    } catch (Throwable ignored) {
                    }

                    if (idName.contains("output")
                            || idName.contains("log")
                            || idName.contains("console")
                            || idName.contains("result")) {
                        return found;
                    }
                }
            }
        }

        return null;
    }

'''

    pos = text.rfind("}")
    if pos < 0:
        log("MainActivity class closing brace tidak ditemukan")
        return

    text = text[:pos] + helper + text[pos:]
    write(MAIN, text)

    # Add installation call after onCreate opening if possible.
    if "installVivoCrashHandler();" not in text:
        pattern = r"(protected\s+void\s+onCreate\s*\([^)]*\)\s*\{)"
        patched, count = re.subn(
            pattern,
            r"\1\n        installVivoCrashHandler();",
            text,
            count=1
        )

        if count:
            write(MAIN, patched)
            log("Crash handler dipasang ke onCreate()")
        else:
            log("onCreate() tidak ditemukan; handler tetap dibuat")

patch_main_crash_handler()

def verify_java_files():
    log("")
    log("=== Verification ===")

    for path in (MAIN, USB):
        if not path.exists():
            continue

        text = read(path)

        braces = text.count("{") - text.count("}")

        log(
            path.name
            + ": braces="
            + str(braces)
            + ", chars="
            + str(len(text))
        )

        if braces != 0:
            log("WARNING: jumlah {} tidak seimbang pada " + str(path))

    log("Patch selesai.")
    log("Backup .bak dibuat sebelum perubahan.")
    log("")
    log("Selanjutnya build project dengan Gradle.")
    log("Jangan menjalankan unlock sebelum memastikan command Vivo")
    log("yang sesuai dengan firmware/device terdeteksi.")

verify_java_files()
