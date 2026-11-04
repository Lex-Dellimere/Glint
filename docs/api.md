# Glint API

Import `"glint/glint"` for everything below except the math, which is `"glint/glint_math"`.
Every Glint name starts with `glint_`, `Glint` or `GLINT_`; GL itself keeps its own names (`glClear`, `GL_TRIANGLES`).

## Contexts

| Function | What it does |
|----------|--------------|
| `glint_config() -> GlintConfig` | The default settings: GL 4.6 wanted, 3.3 accepted, vsync on, 24-bit depth, 8-bit stencil. |
| `glint_open_window(title: string, w, h: int32, cfg: GlintConfig*) -> GlintContext*` | A new window with a current context. |
| `glint_open_existing(handle: int64, cfg) -> GlintContext*` | A context on your window: X11 window id or HWND. Your program keeps its events. |
| `glint_open_headless(w, h: int32, cfg) -> GlintContext*` | No window. Draws into an off-screen framebuffer, bound on return. |
| `glint_open_shared(parent, w, h) -> GlintContext*` | An off-screen context sharing textures, buffers and shaders with `parent`. It draws into a texture, `glint_color_texture(ctx)`, that `parent` can draw. It is current on return: `glint_make_current(parent)` goes back. Finish its drawing (`glFinish` or a fence) before `parent` reads the texture. |
| `glint_x11_visual(cfg, &visual_id: int64, &depth: int32) -> bool` | Linux: the X visual and depth to make your own window with before `glint_open_existing`. Make a colormap for that visual too. False on Windows. |
| `glint_close(ctx)` | Frees the context, and the window if Glint made it. |
| `glint_make_current(ctx) -> bool` | Makes this context current on the calling thread. |
| `glint_swap(ctx)` | Shows the frame. For headless contexts it only flushes. |
| `glint_swap_damage(ctx, rects: int32*, n) -> bool` | Shows the frame, telling the system only `n` rectangles (x, y, w, h from the top-left) changed. Uses `EGL_KHR`/`EXT_swap_buffers_with_damage`; elsewhere it does a full swap and returns false. |
| `glint_buffer_age(ctx) -> int32` | Ask before drawing a frame: how many frames old the back buffer is (1 = last frame's picture is there). 0 = unknown, so redraw everything. EGL and GLX with `*_EXT_buffer_age`; always 0 on WGL. |
| `glint_set_vsync(ctx, n: int32) -> bool` | Swap interval: 1 waits for vblank, 0 does not. |
| `glint_resize(ctx, w, h) -> bool` | Own window: resizes it. Headless: makes a new framebuffer. Existing window: records the size. |
| `glint_set_title(ctx, title: string)` | Own window only. |
| `glint_error() -> cstring` | Why the last call failed. |
| `glint_getproc(name: cstring) -> int64` | The address of any GL function, for names Glint does not declare. |
| `glint_time() -> float64` | Seconds from a fixed point, for frame timing. |

`GlintConfig` fields: `major`, `minor` (lowest version accepted), `want_major`, `want_minor` (tried first), `debug`, `vsync`, `depth_bits`, `stencil_bits`, `samples`, `srgb`, `resizable`, `visible`, `backend` (`GLINT_BACKEND_AUTO`, `_EGL`, `_GLX`, `_WGL`).

Read-only facts about a context:

| Function | Gives |
|----------|-------|
| `glint_width(ctx)`, `glint_height(ctx)` | Drawable size, kept up to date by resize events. |
| `glint_gl_version(ctx) -> int32` | Version as major * 10 + minor (46, 45, ...). Also `ctx->gl_major`, `ctx->gl_minor`. |
| `glint_backend_name(ctx) -> string` | `"EGL"`, `"GLX"` or `"WGL"`. |
| `glint_framebuffer(ctx) -> uint32` | The framebuffer that means "the screen": 0 for windows, the off-screen one when headless. |
| `glint_has_ext(name: string) -> bool` | Whether the current context has an extension, e.g. `"GL_ARB_bindless_texture"`. |

## Events (own window)

```mettle
var ev: GlintEvent;
while (glint_poll(ctx, &ev)) { ... }
```

| `ev.kind` | Fields |
|-----------|--------|
| `GLINT_EV_CLOSE` | The user closed the window. `glint_should_close(ctx)` is now true. |
| `GLINT_EV_RESIZE` | `w`, `h`: new size. Call `glViewport`. |
| `GLINT_EV_KEY_DOWN`, `GLINT_EV_KEY_UP` | `key` (a `GLINT_KEY_*` code), `mods` (`GLINT_MOD_SHIFT`, `_CTRL`, `_ALT`). |
| `GLINT_EV_MOUSE_MOVE` | `x`, `y` from the top-left. |
| `GLINT_EV_MOUSE_DOWN`, `GLINT_EV_MOUSE_UP` | `button` (`GLINT_MOUSE_LEFT`, `_MIDDLE`, `_RIGHT`), `x`, `y`. |
| `GLINT_EV_SCROLL` | `dy`: 1 up, -1 down. |
| `GLINT_EV_FOCUS` | `x`: 1 gained, 0 lost. |

Key codes: letters and digits are their upper-case ASCII codes (`'A'` = 65), space is 32, and named keys are `GLINT_KEY_ESCAPE`, `_ENTER`, `_TAB`, `_BACKSPACE`, `_INSERT`, `_DELETE`, `_LEFT`, `_RIGHT`, `_UP`, `_DOWN`, `_PAGE_UP`, `_PAGE_DOWN`, `_HOME`, `_END`, `_F1` (F1 to F12 are `GLINT_KEY_F1 + 0..11`), `_LEFT_SHIFT`, `_LEFT_CTRL`, `_LEFT_ALT` and the right-hand ones.

State you can ask for at any time: `glint_key_down(ctx, key)`, `glint_mouse_down(ctx, button)`, `ctx->mouse_x`, `ctx->mouse_y`, `glint_should_close(ctx)`, `glint_set_should_close(ctx, bool)`.

With `glint_open_existing` your program owns the window and its events; `glint_poll` returns nothing.

If `glint_open_existing` fails it returns 0 and never ends your program: on X11, errors are caught while Glint works on your window, and everything Glint made is freed. The window stays as it was, so you can keep presenting into it another way (on Windows, see the note on pixel formats in [platforms.md](platforms.md)).

## Helpers

| Function | What it does |
|----------|--------------|
| `glint_shader(kind: uint32, src: string) -> uint32` | Compiles one shader. 0 on failure, with the log in `glint_error()`. |
| `glint_program(vs: string, fs: string) -> uint32` | Compiles and links a vertex and fragment shader. 0 on failure. |
| `glint_uniform(prog, name: cstring) -> int32` | `glGetUniformLocation`. |
| `glint_enable_debug_output() -> bool` | Prints driver debug messages to stderr. Use with `cfg.debug = true`. |
| `glint_read_rect(ctx, x, y, w, h, format, out: uint8*, stride: int32)` | Reads a rectangle, top row first, (x, y) from the top-left. `format` is `GLINT_FORMAT_RGBA` or `GLINT_FORMAT_BGRA`. `stride` is the bytes between rows of `out` (0 = w * 4, else a multiple of 4), so a tile can go straight into a bigger image. |
| `glint_read_rgba(ctx, out: uint8*)` | Reads the whole drawable as RGBA8, top row first. `out` holds width * height * 4 bytes. |
| `glint_read_pixel(ctx, x, y) -> uint32` | One pixel as 0xAARRGGBB, (x, y) from the top-left. |
| `glint_write_ppm(path: cstring, w, h, rgba: uint8*) -> bool` | Saves RGBA pixels as a PPM image. |

In Mettle strings, `{` starts an interpolation, so write `{{` for a literal brace in GLSL: `"void main() {{ ... }"`.

## The GL functions

`glint_gl` declares each GL 4.6 core function as a function pointer, filled when a context is made. A comment above each one gives its C signature. `glint_load_gl(getproc)` refills them (it returns how many were missing); you only need it if you make a context some other way. `GLINT_GL_FUNCTION_COUNT` is 657.

`glint_ext` does the same for ARB, KHR and EXT extensions, filled by `glint_load_ext(getproc)`. `GLINT_EXT_NAMES` lists every extension name `gl.xml` has for desktop GL.

Only the core profile is covered: functions that core 3.2 removed (`glBegin`, `glMatrixMode` and the like) are not declared.

## Math (`glint/glint_math`)

`GlintVec3 { x, y, z }` and `GlintMat4 { m: float32[16] }`, column by column like GL, so `glUniformMatrix4fv(loc, 1, (uint8)0, &m.m[0])` works. Angles are in radians.

`glint_vec3`, `glint_vec3_add`, `_sub`, `_scale`, `_dot`, `_cross`, `_length`, `_normalize`;
`glint_mat4_identity`, `glint_mat4_mul(a, b)` (b applies first), `glint_mat4_translate`, `glint_mat4_scale`, `glint_mat4_rotate(angle, axis)`, `glint_mat4_perspective(fovy, aspect, near, far)`, `glint_mat4_ortho`, `glint_mat4_look_at(eye, center, up)`;
`glint_radians`, `glint_sin`, `glint_cos`, `glint_tan`, `glint_sqrt`, `GLINT_PI`.
