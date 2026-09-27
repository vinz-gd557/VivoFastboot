# VivoFastboot

Android USB-host fastboot utility inspired by the dark UI in the supplied screenshot.

## What this project does

- Detects USB devices attached through USB-OTG.
- Requests USB permission using Android's `UsbManager`.
- Talks to a fastboot bootloader directly over bulk USB endpoints.
- `getvar:all`, selected partition information, reboot, flash, erase, format command, and reboot/bootloader actions.
- Vivo-specific bootloader commands exposed by the supplied binary:
  - `vivo_bsp unlock_vivo` / `vivo_bsp lock_vivo`
  - `bbk unlock_vivo` / `bbk lock_vivo`
  - plus generic `flashing unlock` / `flashing lock` fallback.
- `disable-verity` and `disable-verification` can patch an AVB vbmeta image before flashing it. AOSP documents these flags as bit 0 and bit 1 in the AVB vbmeta header. The normal flash path streams the selected file instead of loading a large image into RAM. 
- A recoverable action layer catches exceptions and writes them to the in-app Output panel.

## Important limitations

No Android app can honestly guarantee "100% no crash" or that every Vivo model accepts every fastboot command. Vivo bootloaders differ by generation/region/software, some expose vendor-specific restrictions, and an unsupported command must be reported as a failure instead of being guessed.

The uploaded `vendor/fastboot-arm64-android` is kept as a reference binary. It is an ARM64 Android executable and its strings show the Vivo-specific commands above. This app does **not** run that binary directly; instead it uses Android USB Host APIs so it can communicate with the connected phone without relying on `/dev/bus/usb` access from a child process.

Before publishing the binary to GitHub, verify that you have permission/license to redistribute it.

## Build

Use Android Studio or a Gradle installation with Android SDK 35.

```bash
gradle :app:assembleDebug
```

APK:

```text
app/build/outputs/apk/debug/app-debug.apk
```

## Hardware

The host Android phone needs USB host/OTG support. The target phone must expose a compatible fastboot USB interface.

## GitHub Actions

This repository includes `.github/workflows/android.yml`.
Push the project to GitHub and open **Actions**. The workflow builds both debug and release APKs and uploads them as GitHub Actions artifacts.

To trigger a build manually, open the workflow and choose **Run workflow**.
