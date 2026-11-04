#!/usr/bin/env python3
"""Make Glint's GL bindings from the Khronos registry (registry/gl.xml).

Writes:
  src/glint_gl.mettle   every GL 4.6 core enum and function, and glint_load_gl
  src/glint_ext.mettle  ARB, KHR and EXT extensions (what core lacks), and glint_load_ext

Run it with `mbuild gen` or `python3 tools/glgen.py`. It uses only the Python
standard library. Only re-run it when gl.xml changes; the output is committed.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML = os.path.join(ROOT, "registry", "gl.xml")
EXT_PREFIXES = ("GL_ARB_", "GL_KHR_", "GL_EXT_")

# GL type -> Mettle type
BASE = {
    "GLenum": "uint32", "GLbitfield": "uint32", "GLuint": "uint32", "GLint": "int32",
    "GLsizei": "int32", "GLboolean": "uint8", "GLbyte": "int8", "GLubyte": "uint8",
    "GLshort": "int16", "GLushort": "uint16", "GLfloat": "float32", "GLclampf": "float32",
    "GLdouble": "float64", "GLclampd": "float64", "GLchar": "uint8", "GLcharARB": "uint8",
    "GLint64": "int64", "GLuint64": "uint64", "GLint64EXT": "int64", "GLuint64EXT": "uint64",
    "GLintptr": "int64", "GLsizeiptr": "int64", "GLintptrARB": "int64", "GLsizeiptrARB": "int64",
    "GLhalf": "uint16", "GLhalfARB": "uint16", "GLhalfNV": "uint16", "GLfixed": "int32",
    "GLclampx": "int32", "GLhandleARB": "uint32", "GLvdpauSurfaceNV": "int64",
    "GLsync": "rawptr", "GLeglImageOES": "rawptr", "GLeglClientBufferEXT": "rawptr",
    "void": "void", "GLvoid": "void",
}
# GLDEBUGPROC and friends: a Mettle fn with this shape can be passed with &name.
DEBUGPROC = "fn(uint32, uint32, uint32, uint32, int32, cstring, rawptr) -> void"
CALLBACKS = {"GLDEBUGPROC": DEBUGPROC, "GLDEBUGPROCARB": DEBUGPROC, "GLDEBUGPROCKHR": DEBUGPROC,
             "GLDEBUGPROCAMD": "fn(uint32, uint32, uint32, int32, cstring, rawptr) -> void",
             "GLVULKANPROCNV": "fn() -> void"}


def ctype(elem, skip_name=True):
    """Return (C text, base type, star count) for a <proto> or <param>."""
    parts = []
    base = None
    if elem.text:
        parts.append(elem.text)
    for ch in elem:
        if ch.tag == "ptype":
            base = ch.text
            parts.append(ch.text)
        elif ch.tag == "name":
            if not skip_name:
                parts.append(ch.text)
        if ch.tail:
            parts.append(ch.tail)
    text = " ".join("".join(parts).split())
    stars = text.count("*")
    if base is None or "struct _cl" in text:
        m = re.search(r"\b(void|GLvoid)\b", text)
        base = m.group(1) if m else "void"
    return text, base, stars


def mtype(text, base, stars):
    if base in CALLBACKS and stars == 0:
        return CALLBACKS[base]
    t = BASE.get(base)
    if t is None:
        sys.exit("glgen: unknown GL type %r in %r" % (base, text))
    const_char = base in ("GLchar", "GLcharARB", "GLubyte") and text.startswith("const")
    if stars == 0:
        return t
    if t == "void":
        return "rawptr" + "*" * (stars - 1)
    if const_char and stars == 1:
        return "cstring"
    if const_char and stars == 2:
        return "cstring*"
    return t + "*" * stars


def load():
    reg = ET.parse(XML).getroot()
    enums = {}  # name -> (value, type)
    for grp in reg.iter("enums"):
        for e in grp.findall("enum"):
            if e.get("api") not in (None, "gl"):
                continue
            enums[e.get("name")] = (e.get("value"), e.get("type"))
    cmds = {}
    for c in reg.find("commands").findall("command"):
        proto = c.find("proto")
        name = proto.find("name").text
        rt, rb, rs = ctype(proto)
        params = []
        for p in c.findall("param"):
            if p.get("api") not in (None, "gl"):
                continue
            pt, pb, ps = ctype(p)
            params.append((p.find("name").text, pt, pb, ps))
        cmds[name] = ((rt, rb, rs), params)
    return reg, enums, cmds


def core(reg):
    """Enum and command names of GL 4.6 core, in registry order."""
    en, cm = [], []
    for f in reg.findall("feature"):
        if f.get("api") != "gl" or float(f.get("number")) > 4.6:
            continue
        for r in f.findall("require"):
            if r.get("profile") == "compatibility":
                continue
            for e in r.findall("enum"):
                en.append(e.get("name"))
            for c in r.findall("command"):
                cm.append(c.get("name"))
        for r in f.findall("remove"):
            if r.get("profile") not in (None, "core"):
                continue
            gone = {e.get("name") for e in r.findall("enum")} | {c.get("name") for c in r.findall("command")}
            en = [n for n in en if n not in gone]
            cm = [n for n in cm if n not in gone]
    return dedupe(en), dedupe(cm)


def dedupe(xs):
    seen, out = set(), []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def extensions(reg):
    out = []
    for x in reg.find("extensions").findall("extension"):
        name = x.get("name")
        sup = x.get("supported", "").split("|")
        if not name.startswith(EXT_PREFIXES) or not ("gl" in sup or "glcore" in sup):
            continue
        en, cm = [], []
        for r in x.findall("require"):
            if r.get("api") not in (None, "gl") or r.get("profile") == "compatibility":
                continue
            en += [e.get("name") for e in r.findall("enum")]
            cm += [c.get("name") for c in r.findall("command")]
        out.append((name, dedupe(en), dedupe(cm)))
    return out


def const_line(name, val, typ):
    t = "uint32"
    if typ == "ull":
        t = "uint64"
    v = val
    if v.startswith("-"):
        t = "int32"
    elif v.startswith("0x") and len(v) > 10:
        t = "uint64"
    return "export const %s: %s = %s;" % (name, t, v)


def sig(cmds, name):
    (rt, rb, rs), params = cmds[name]
    args = ", ".join(mtype(pt, pb, ps) for _, pt, pb, ps in params)
    return "fn(%s) -> %s" % (args, mtype(rt, rb, rs))


def c_doc(cmds, name):
    (rt, _, _), params = cmds[name]
    return "// %s %s(%s)" % (rt, name, ", ".join("%s %s" % (pt, pn) for pn, pt, _, _ in params))


def emit_cmds(lines, cmds, names):
    for n in names:
        lines.append(c_doc(cmds, n))
        lines.append("export var %s: %s = 0;" % (n, sig(cmds, n)))


def emit_loader(lines, cmds, names, fn_name, what):
    # Mettle compiles one huge function very slowly (657 lines: 2.8 s; in parts
    # of 32: 0.1 s), so the loader is split into small private parts.
    part = fn_name + "_part"
    chunks = [names[i:i + 32] for i in range(0, len(names), 32)]
    for k, chunk in enumerate(chunks):
        lines.append("")
        lines.append("fn %s%d(glint_getproc_cb: fn(cstring) -> int64) -> int32 {" % (part, k))
        lines.append("  var miss: int32 = 0;")
        lines.append("  var p: int64 = 0;")
        for n in chunk:
            lines.append('  p = glint_getproc_cb("%s"); if (p == 0) { miss += 1; } %s = (%s)p;' % (n, n, sig(cmds, n)))
        lines.append("  return miss;")
        lines.append("}")
    lines.append("")
    lines.append("// Fill every %s function pointer with glint_getproc_cb. A name the driver" % what)
    lines.append("// does not give stays 0. Returns how many were missing.")
    lines.append("export fn %s(glint_getproc_cb: fn(cstring) -> int64) -> int32 {" % fn_name)
    lines.append("  var miss: int32 = 0;")
    for k in range(len(chunks)):
        lines.append("  miss += %s%d(glint_getproc_cb);" % (part, k))
    lines.append("  return miss;")
    lines.append("}")


HEADER = """// GENERATED by tools/glgen.py from registry/gl.xml. Do not edit by hand.
// gl.xml is Copyright 2013-2026 The Khronos Group Inc., Apache-2.0.
"""


def main():
    reg, enums, cmds = load()
    cen, ccm = core(reg)
    core_en, core_cm = set(cen), set(ccm)

    L = [HEADER, "// OpenGL 4.6 core profile: %d enums, %d functions." % (len(cen), len(ccm)),
         "// Types: GLenum/GLbitfield/GLuint = uint32, GLint/GLsizei = int32, GLboolean = uint8,",
         "// GLfloat = float32, GLintptr/GLsizeiptr = int64, const GLchar* = cstring, void* = rawptr.", ""]
    for n in cen:
        L.append(const_line(n, *enums[n]))
    L.append("")
    emit_cmds(L, cmds, ccm)
    emit_loader(L, cmds, ccm, "glint_load_gl", "GL 4.6 core")
    L.append("")
    L.append("export const GLINT_GL_FUNCTION_COUNT: int32 = %d;" % len(ccm))
    write("src/glint_gl.mettle", L)

    exts = extensions(reg)
    seen_en, seen_cm = set(core_en), set(core_cm)
    E = [HEADER, "// ARB, KHR and EXT extensions for desktop GL. Only names that GL 4.6 core does",
         "// not already have are here; an extension promoted to core keeps its core names in",
         "// glint_gl. Check glint_has_ext(\"GL_ARB_...\") before calling one of these.", ""]
    ext_cmds = []
    for name, en, cm in exts:
        new_en = [e for e in en if e not in seen_en and e in enums]
        new_cm = [c for c in cm if c not in seen_cm and c in cmds]
        seen_en.update(new_en)
        seen_cm.update(new_cm)
        if not new_en and not new_cm:
            continue
        E.append("// ---- %s" % name)
        for e in new_en:
            E.append(const_line(e, *enums[e]))
        emit_cmds(E, cmds, new_cm)
        ext_cmds += new_cm
    emit_loader(E, cmds, ext_cmds, "glint_load_ext", "extension")
    E.append("")
    E.append("// Every ARB/KHR/EXT extension name gl.xml lists for desktop GL.")
    E.append("export const GLINT_EXT_COUNT: int32 = %d;" % len(exts))
    E.append("export const GLINT_EXT_NAMES: string[%d] = [" % len(exts))
    E.append(",\n".join('  "%s"' % n for n, _, _ in exts))
    E.append("];")
    write("src/glint_ext.mettle", E)
    print("glgen: core %d enums %d fns; %d extensions, %d extension fns" % (len(cen), len(ccm), len(exts), len(ext_cmds)))


def write(rel, lines):
    with open(os.path.join(ROOT, rel), "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
