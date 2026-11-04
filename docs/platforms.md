# How Glint works on each platform

## Linux

Glint loads these with `dlopen` when you make the first context: `libEGL.so.1`, `libX11.so.6`, and for GLX `libGLX.so.0` (or `libGL.so.1`). `libOpenGL.so.0` is used to find GL functions that EGL does not hand out. Because of `dlopen`, a program that uses Glint links against libc (`mbuild` does this for you). Programs that don't import Glint stay static.

**Own window.** Glint opens the X display named by `DISPLAY`, makes a window with the visual the GL config wants, and asks for `WM_DELETE_WINDOW` so closing it gives `GLINT_EV_CLOSE`. Then it tries EGL (`EGL_PLATFORM_X11_KHR`) and, if that fails, GLX (`glXCreateContextAttribsARB`). Set `cfg.backend` to force one.

**Existing window.** Pass the X11 window id. Glint opens its own connection to the same X server for GL, picks a config with the window's visual, and leaves your connection and events alone. This works with windows made through libX11, libxcb, or a program that speaks the X protocol itself.

**Headless.** EGL only, no X server needed. Glint tries, in order: an EGL device (`EGL_EXT_device_enumeration`, a real GPU), Mesa's surfaceless platform, then the default display. The context is made current without a surface and draws into a framebuffer object. Set `GLINT_EGL_PLATFORM=surfaceless` to skip the device step.

With glvnd, `__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json` picks Mesa, and `LIBGL_ALWAYS_SOFTWARE=1` its software renderer (llvmpipe, GL 4.5).

**Not covered:** Wayland (use XWayland), GLX headless (pbuffers).

## Windows

Glint loads `opengl32.dll` with `LoadLibraryA`; the program links `user32` and `gdi32` (mbuild does it). WGL needs a context before it hands out `wglChoosePixelFormatARB` and `wglCreateContextAttribsARB`, so the first context also makes and drops a hidden throwaway window.

**Own window.** A window of the class `GlintWindow` with Glint's window procedure, which turns messages into `GlintEvent`s. `glint_poll` runs the message loop.

**Existing window.** Pass the HWND. If the window has no pixel format yet, Glint picks and sets one (Windows allows this once per window). Your window procedure keeps handling messages.

**Headless.** WGL always needs a window, so Glint makes a hidden one and draws into a framebuffer object.

## Under wine

The Windows build runs under wine, which maps WGL onto the host's GLX. `mbuild wintest` builds the tests for Windows and runs them on a private Xvfb (`:96`), so nothing appears on your screen. It needs a Windows build of the Mettle compiler in `MBUILD_METTLE_WINDOWS`.

## Versions

Glint asks for `want_major.want_minor` (4.6) and steps down to `major.minor` (3.3): 4.6, 4.5, 4.4, 4.3, 4.2, 4.1, 4.0, 3.3. It always asks for a core profile. On this project's test machine: NVIDIA gives 4.6 headless, Mesa llvmpipe gives 4.5 (Xvfb, wine and surfaceless).
