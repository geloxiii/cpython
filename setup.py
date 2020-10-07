# # Autodetecting setup.py script for building the Python extensions

# import argparse
# import importlib._bootstrap
# import importlib.machinery
# import importlib.util
# import os
# import re
# import sys
# import sysconfig
# from distutils import log

# # from distutils.command.build_ext import build_ext
# # from distutils.command.build_scripts import build_scripts
# # from distutils.command.install import install
# # from distutils.command.install_lib import install_lib
# from distutils.core import Extension, setup
# from distutils.errors import CCompilerError, DistutilsError
# from distutils.spawn import find_executable
# from glob import escape, glob

# # Compile extensions used to test Python?
# TEST_EXTENSIONS = True

# # This global variable is used to hold the list of modules to be disabled.
# DISABLED_MODULE_LIST = []


# def get_platform():
#     # Cross compiling
#     if "_PYTHON_HOST_PLATFORM" in os.environ:
#         return os.environ["_PYTHON_HOST_PLATFORM"]

#     # Get value of sys.platform
#     if sys.platform.startswith('osf1'):
#         return 'osf1'
#     return sys.platform


# CROSS_COMPILING = "_PYTHON_HOST_PLATFORM" in os.environ
# HOST_PLATFORM = get_platform()
# MS_WINDOWS = HOST_PLATFORM == 'win32'
# CYGWIN = HOST_PLATFORM == 'cygwin'
# MACOS = HOST_PLATFORM == 'darwin'
# AIX = HOST_PLATFORM.startswith('aix')
# VXWORKS = 'vxworks' in HOST_PLATFORM


# SUMMARY = """
# Python is an interpreted, interactive, object-oriented programming
# language. It is often compared to Tcl, Perl, Scheme or Java.

# Python combines remarkable power with very clear syntax. It has
# modules, classes, exceptions, very high level dynamic data types, and
# dynamic typing. There are interfaces to many system calls and
# libraries, as well as to various windowing systems (X11, Motif, Tk,
# Mac, MFC). New built-in modules are easily written in C or C++. Python
# is also usable as an extension language for applications that need a
# programmable interface.

# The Python implementation is portable: it runs on many brands of UNIX,
# on Windows, DOS, Mac, Amiga... If your favorite system isn't
# listed here, it may still be supported, if there's a C compiler for
# it. Ask around on comp.lang.python -- or just try compiling Python
# yourself.
# """

# CLASSIFIERS = """
# Development Status :: 6 - Mature
# License :: OSI Approved :: Python Software Foundation License
# Natural Language :: English
# Programming Language :: C
# Programming Language :: Python
# Topic :: Software Development
# """


# def run_command(cmd):
#     status = os.system(cmd)
#     return os.waitstatus_to_exitcode(status)


# # Set common compiler and linker flags derived from the Makefile,
# # reserved for building the interpreter and the stdlib modules.
# # See bpo-21121 and bpo-35257
# def set_compiler_flags(compiler_flags, compiler_py_flags_nodist):
#     flags = sysconfig.get_config_var(compiler_flags)
#     py_flags_nodist = sysconfig.get_config_var(compiler_py_flags_nodist)
#     sysconfig.get_config_vars()[compiler_flags] = flags + ' ' + py_flags_nodist


# def add_dir_to_list(dirlist, dir):
#     """Add the directory 'dir' to the list 'dirlist' (after any relative
#     directories) if:

#     1) 'dir' is not already in 'dirlist'
#     2) 'dir' actually exists, and is a directory.
#     """
#     if dir is None or not os.path.isdir(dir) or dir in dirlist:
#         return
#     for i, path in enumerate(dirlist):
#         if not os.path.isabs(path):
#             dirlist.insert(i + 1, dir)
#             return
#     dirlist.insert(0, dir)


# def sysroot_paths(make_vars, subdirs):
#     """Get the paths of sysroot sub-directories.

#     * make_vars: a sequence of names of variables of the Makefile where
#       sysroot may be set.
#     * subdirs: a sequence of names of subdirectories used as the location for
#       headers or libraries.
#     """

#     dirs = []
#     for var_name in make_vars:
#         var = sysconfig.get_config_var(var_name)
#         if var is not None:
#             m = re.search(r'--sysroot=([^"]\S*|"[^"]+")', var)
#             if m is not None:
#                 sysroot = m.group(1).strip('"')
#                 for subdir in subdirs:
#                     if os.path.isabs(subdir):
#                         subdir = subdir[1:]
#                     path = os.path.join(sysroot, subdir)
#                     if os.path.isdir(path):
#                         dirs.append(path)
#                 break
#     return dirs


# MACOS_SDK_ROOT = None
# MACOS_SDK_SPECIFIED = None


# def macosx_sdk_root():
#     """Return the directory of the current macOS SDK.

#     If no SDK was explicitly configured, call the compiler to find which
#     include files paths are being searched by default.  Use '/' if the
#     compiler is searching /usr/include (meaning system header files are
#     installed) or use the root of an SDK if that is being searched.
#     (The SDK may be supplied via Xcode or via the Command Line Tools).
#     The SDK paths used by Apple-supplied tool chains depend on the
#     setting of various variables; see the xcrun man page for more info.
#     Also sets MACOS_SDK_SPECIFIED for use by macosx_sdk_specified().
#     """
#     global MACOS_SDK_ROOT, MACOS_SDK_SPECIFIED

#     # If already called, return cached result.
#     if MACOS_SDK_ROOT:
#         return MACOS_SDK_ROOT

#     cflags = sysconfig.get_config_var('CFLAGS')
#     m = re.search(r'-isysroot\s*(\S+)', cflags)
#     if m is not None:
#         MACOS_SDK_ROOT = m.group(1)
#         MACOS_SDK_SPECIFIED = MACOS_SDK_ROOT != '/'
#     else:
#         MACOS_SDK_ROOT = '/'
#         MACOS_SDK_SPECIFIED = False
#         cc = sysconfig.get_config_var('CC')
#         tmpfile = '/tmp/setup_sdk_root.%d' % os.getpid()
#         try:
#             os.unlink(tmpfile)
#         except:
#             pass
#         ret = run_command('%s -E -v - </dev/null 2>%s 1>/dev/null' % (cc, tmpfile))
#         in_incdirs = False
#         try:
#             if ret == 0:
#                 with open(tmpfile) as fp:
#                     for line in fp.readlines():
#                         if line.startswith("#include <...>"):
#                             in_incdirs = True
#                         elif line.startswith("End of search list"):
#                             in_incdirs = False
#                         elif in_incdirs:
#                             line = line.strip()
#                             if line == '/usr/include':
#                                 MACOS_SDK_ROOT = '/'
#                             elif line.endswith(".sdk/usr/include"):
#                                 MACOS_SDK_ROOT = line[:-12]
#         finally:
#             os.unlink(tmpfile)

#     return MACOS_SDK_ROOT


# def macosx_sdk_specified():
#     """Returns true if an SDK was explicitly configured.

#     True if an SDK was selected at configure time, either by specifying
#     --enable-universalsdk=(something other than no or /) or by adding a
#     -isysroot option to CFLAGS.  In some cases, like when making
#     decisions about macOS Tk framework paths, we need to be able to
#     know whether the user explicitly asked to build with an SDK versus
#     the implicit use of an SDK when header files are no longer
#     installed on a running system by the Command Line Tools.
#     """
#     global MACOS_SDK_SPECIFIED

#     # If already called, return cached result.
#     if MACOS_SDK_SPECIFIED:
#         return MACOS_SDK_SPECIFIED

#     # Find the sdk root and set MACOS_SDK_SPECIFIED
#     macosx_sdk_root()
#     return MACOS_SDK_SPECIFIED


# def is_macosx_sdk_path(path):
#     """
#     Returns True if 'path' can be located in an OSX SDK
#     """
#     return (
#         (path.startswith('/usr/') and not path.startswith('/usr/local'))
#         or path.startswith('/System/')
#         or path.startswith('/Library/')
#     )


# def find_file(filename, std_dirs, paths):
#     """Searches for the directory where a given file is located,
#     and returns a possibly-empty list of additional directories, or None
#     if the file couldn't be found at all.

#     'filename' is the name of a file, such as readline.h or libcrypto.a.
#     'std_dirs' is the list of standard system directories; if the
#         file is found in one of them, no additional directives are needed.
#     'paths' is a list of additional locations to check; if the file is
#         found in one of them, the resulting list will contain the directory.
#     """
#     if MACOS:
#         # Honor the MacOSX SDK setting when one was specified.
#         # An SDK is a directory with the same structure as a real
#         # system, but with only header files and libraries.
#         sysroot = macosx_sdk_root()

#     # Check the standard locations
#     for dir in std_dirs:
#         f = os.path.join(dir, filename)

#         if MACOS and is_macosx_sdk_path(dir):
#             f = os.path.join(sysroot, dir[1:], filename)

#         if os.path.exists(f):
#             return []

#     # Check the additional directories
#     for dir in paths:
#         f = os.path.join(dir, filename)

#         if MACOS and is_macosx_sdk_path(dir):
#             f = os.path.join(sysroot, dir[1:], filename)

#         if os.path.exists(f):
#             return [dir]

#     # Not found anywhere
#     return None


# def find_library_file(compiler, libname, std_dirs, paths):
#     result = compiler.find_library_file(std_dirs + paths, libname)
#     if result is None:
#         return None

#     if MACOS:
#         sysroot = macosx_sdk_root()

#     # Check whether the found file is in one of the standard directories
#     dirname = os.path.dirname(result)
#     for p in std_dirs:
#         # Ensure path doesn't end with path separator
#         p = p.rstrip(os.sep)

#         if MACOS and is_macosx_sdk_path(p):
#             # Note that, as of Xcode 7, Apple SDKs may contain textual stub
#             # libraries with .tbd extensions rather than the normal .dylib
#             # shared libraries installed in /.  The Apple compiler tool
#             # chain handles this transparently but it can cause problems
#             # for programs that are being built with an SDK and searching
#             # for specific libraries.  Distutils find_library_file() now
#             # knows to also search for and return .tbd files.  But callers
#             # of find_library_file need to keep in mind that the base filename
#             # of the returned SDK library file might have a different extension
#             # from that of the library file installed on the running system,
#             # for example:
#             #   /Applications/Xcode.app/Contents/Developer/Platforms/
#             #       MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk/
#             #       usr/lib/libedit.tbd
#             # vs
#             #   /usr/lib/libedit.dylib
#             if os.path.join(sysroot, p[1:]) == dirname:
#                 return []

#         if p == dirname:
#             return []

#     # Otherwise, it must have been in one of the additional directories,
#     # so we have to figure out which one.
#     for p in paths:
#         # Ensure path doesn't end with path separator
#         p = p.rstrip(os.sep)

#         if MACOS and is_macosx_sdk_path(p):
#             if os.path.join(sysroot, p[1:]) == dirname:
#                 return [p]

#         if p == dirname:
#             return [p]
#     else:
#         assert False, "Internal error: Path not found in std_dirs or paths"


# def validate_tzpath():
#     base_tzpath = sysconfig.get_config_var('TZPATH')
#     if not base_tzpath:
#         return

#     tzpaths = base_tzpath.split(os.pathsep)
#     bad_paths = [tzpath for tzpath in tzpaths if not os.path.isabs(tzpath)]
#     if bad_paths:
#         raise ValueError(
#             'TZPATH must contain only absolute paths, '
#             + f'found:\n{tzpaths!r}\nwith invalid paths:\n'
#             + f'{bad_paths!r}'
#         )


# def find_module_file(module, dirlist):
#     """Find a module in a set of possible folders. If it is not found
#     return the unadorned filename"""
#     list = find_file(module, [], dirlist)
#     if not list:
#         return module
#     if len(list) > 1:
#         log.info("WARNING: multiple copies of %s found", module)
#     return os.path.join(list[0], module)


# class PyBuildExt(build_ext):
#     def __init__(self, dist):
#         build_ext.__init__(self, dist)
#         self.srcdir = None
#         self.lib_dirs = None
#         self.inc_dirs = None
#         self.config_h_vars = None
#         self.failed = []
#         self.failed_on_import = []
#         self.missing = []
#         self.disabled_configure = []
#         if '-j' in os.environ.get('MAKEFLAGS', ''):
#             self.parallel = True

#     def add(self, ext):
#         self.extensions.append(ext)

#     def set_srcdir(self):
#         self.srcdir = sysconfig.get_config_var('srcdir')
#         if not self.srcdir:
#             # Maybe running on Windows but not using CYGWIN?
#             raise ValueError("No source directory; cannot proceed.")
#         self.srcdir = os.path.abspath(self.srcdir)

#     def remove_disabled(self):
#         # Remove modules that are present on the disabled list
#         extensions = [ext for ext in self.extensions if ext.name not in DISABLED_MODULE_LIST]
#         # move ctypes to the end, it depends on other modules
#         ext_map = dict((ext.name, i) for i, ext in enumerate(extensions))
#         if "_ctypes" in ext_map:
#             ctypes = extensions.pop(ext_map["_ctypes"])
#             extensions.append(ctypes)
#         self.extensions = extensions

#     def update_sources_depends(self):
#         # Fix up the autodetected modules, prefixing all the source files
#         # with Modules/.
#         moddirlist = [os.path.join(self.srcdir, 'Modules')]

#         # Fix up the paths for scripts, too
#         self.distribution.scripts = [
#             os.path.join(self.srcdir, filename) for filename in self.distribution.scripts
#         ]

#         # Python header files
#         headers = [sysconfig.get_config_h_filename()]
#         headers += glob(os.path.join(escape(sysconfig.get_path('include')), "*.h"))

#         for ext in self.extensions:
#             ext.sources = [find_module_file(filename, moddirlist) for filename in ext.sources]
#             if ext.depends is not None:
#                 ext.depends = [find_module_file(filename, moddirlist) for filename in ext.depends]
#             else:
#                 ext.depends = []
#             # re-compile extensions if a header file has been changed
#             ext.depends.extend(headers)

#     def remove_configured_extensions(self):
#         # The sysconfig variables built by makesetup that list the already
#         # built modules and the disabled modules as configured by the Setup
#         # files.
#         sysconf_built = sysconfig.get_config_var('MODBUILT_NAMES').split()
#         sysconf_dis = sysconfig.get_config_var('MODDISABLED_NAMES').split()

#         mods_built = []
#         mods_disabled = []
#         for ext in self.extensions:
#             # If a module has already been built or has been disabled in the
#             # Setup files, don't build it here.
#             if ext.name in sysconf_built:
#                 mods_built.append(ext)
#             if ext.name in sysconf_dis:
#                 mods_disabled.append(ext)

#         mods_configured = mods_built + mods_disabled
#         if mods_configured:
#             self.extensions = [x for x in self.extensions if x not in mods_configured]
#             # Remove the shared libraries built by a previous build.
#             for ext in mods_configured:
#                 fullpath = self.get_ext_fullpath(ext.name)
#                 if os.path.exists(fullpath):
#                     os.unlink(fullpath)

#         return (mods_built, mods_disabled)

#     def set_compiler_executables(self):
#         # When you run "make CC=altcc" or something similar, you really want
#         # those environment variables passed into the setup.py phase.  Here's
#         # a small set of useful ones.
#         compiler = os.environ.get('CC')
#         args = {}
#         # unfortunately, distutils doesn't let us provide separate C and C++
#         # compilers
#         if compiler is not None:
#             (ccshared, cflags) = sysconfig.get_config_vars('CCSHARED', 'CFLAGS')
#             args['compiler_so'] = compiler + ' ' + ccshared + ' ' + cflags
#         self.compiler.set_executables(**args)

#     def build_extensions(self):
#         self.set_srcdir()

#         # Detect which modules should be compiled
#         self.detect_modules()

#         self.remove_disabled()

#         self.update_sources_depends()
#         mods_built, mods_disabled = self.remove_configured_extensions()
#         self.set_compiler_executables()

#         build_ext.build_extensions(self)

#         if SUBPROCESS_BOOTSTRAP:
#             # Drop our custom subprocess module:
#             # use the newly built subprocess module
#             del sys.modules['subprocess']

#         for ext in self.extensions:
#             self.check_extension_import(ext)

#         self.summary(mods_built, mods_disabled)

#     def summary(self, mods_built, mods_disabled):
#         longest = max([len(e.name) for e in self.extensions], default=0)
#         if self.failed or self.failed_on_import:
#             all_failed = self.failed + self.failed_on_import
#             longest = max(longest, max([len(name) for name in all_failed]))

#         def print_three_column(lst):
#             lst.sort(key=str.lower)
#             # guarantee zip() doesn't drop anything
#             while len(lst) % 3:
#                 lst.append("")
#             for e, f, g in zip(lst[::3], lst[1::3], lst[2::3]):
#                 print("%-*s   %-*s   %-*s" % (longest, e, longest, f, longest, g))

#         if self.missing:
#             print()
#             print("Python build finished successfully!")
#             print("The necessary bits to build these optional modules were not " "found:")
#             print_three_column(self.missing)
#             print(
#                 "To find the necessary bits, look in setup.py in"
#                 " detect_modules() for the module's name."
#             )
#             print()

#         if mods_built:
#             print()
#             print("The following modules found by detect_modules() in" " setup.py, have been")
#             print("built by the Makefile instead, as configured by the" " Setup files:")
#             print_three_column([ext.name for ext in mods_built])
#             print()

#         if mods_disabled:
#             print()
#             print("The following modules found by detect_modules() in" " setup.py have not")
#             print("been built, they are *disabled* in the Setup files:")
#             print_three_column([ext.name for ext in mods_disabled])
#             print()

#         if self.disabled_configure:
#             print()
#             print("The following modules found by detect_modules() in" " setup.py have not")
#             print("been built, they are *disabled* by configure:")
#             print_three_column(self.disabled_configure)
#             print()

#         if self.failed:
#             failed = self.failed[:]
#             print()
#             print("Failed to build these modules:")
#             print_three_column(failed)
#             print()

#         if self.failed_on_import:
#             failed = self.failed_on_import[:]
#             print()
#             print(
#                 "Following modules built successfully"
#                 " but were removed because they could not be imported:"
#             )
#             print_three_column(failed)
#             print()

#         if any('_ssl' in l for l in (self.missing, self.failed, self.failed_on_import)):
#             print()
#             print("Could not build the ssl module!")
#             print(
#                 "Python requires an OpenSSL 1.0.2 or 1.1 compatible "
#                 "libssl with X509_VERIFY_PARAM_set1_host()."
#             )
#             print(
#                 "LibreSSL 2.6.4 and earlier do not provide the necessary "
#                 "APIs, https://github.com/libressl-portable/portable/issues/381"
#             )
#             print()

#     def build_extension(self, ext):

#         if ext.name == '_ctypes':
#             if not self.configure_ctypes(ext):
#                 self.failed.append(ext.name)
#                 return

#         try:
#             build_ext.build_extension(self, ext)
#         except (CCompilerError, DistutilsError) as why:
#             self.announce('WARNING: building of extension "%s" failed: %s' % (ext.name, why))
#             self.failed.append(ext.name)
#             return

#     def check_extension_import(self, ext):
#         # Don't try to import an extension that has failed to compile
#         if ext.name in self.failed:
#             self.announce(
#                 'WARNING: skipping import check for failed build "%s"' % ext.name, level=1
#             )
#             return

#         # Workaround for Mac OS X: The Carbon-based modules cannot be
#         # reliably imported into a command-line Python
#         if 'Carbon' in ext.extra_link_args:
#             self.announce('WARNING: skipping import check for Carbon-based "%s"' % ext.name)
#             return

#         if MACOS and (sys.maxsize > 2 ** 32 and '-arch' in ext.extra_link_args):
#             # Don't bother doing an import check when an extension was
#             # build with an explicit '-arch' flag on OSX. That's currently
#             # only used to build 32-bit only extensions in a 4-way
#             # universal build and loading 32-bit code into a 64-bit
#             # process will fail.
#             self.announce('WARNING: skipping import check for "%s"' % ext.name)
#             return

#         # Workaround for Cygwin: Cygwin currently has fork issues when many
#         # modules have been imported
#         if CYGWIN:
#             self.announce('WARNING: skipping import check for Cygwin-based "%s"' % ext.name)
#             return
#         ext_filename = os.path.join(
#             self.build_lib, self.get_ext_filename(self.get_ext_fullname(ext.name))
#         )

#         # If the build directory didn't exist when setup.py was
#         # started, sys.path_importer_cache has a negative result
#         # cached.  Clear that cache before trying to import.
#         sys.path_importer_cache.clear()

#         # Don't try to load extensions for cross builds
#         if CROSS_COMPILING:
#             return

#         loader = importlib.machinery.ExtensionFileLoader(ext.name, ext_filename)
#         spec = importlib.util.spec_from_file_location(ext.name, ext_filename, loader=loader)
#         try:
#             importlib._bootstrap._load(spec)
#         except ImportError as why:
#             self.failed_on_import.append(ext.name)
#             self.announce(
#                 '*** WARNING: renaming "%s" since importing it' ' failed: %s' % (ext.name, why),
#                 level=3,
#             )
#             assert not self.inplace
#             basename, tail = os.path.splitext(ext_filename)
#             newname = basename + "_failed" + tail
#             if os.path.exists(newname):
#                 os.remove(newname)
#             os.rename(ext_filename, newname)

#         except:
#             exc_type, why, tb = sys.exc_info()
#             self.announce(
#                 '*** WARNING: importing extension "%s" '
#                 'failed with %s: %s' % (ext.name, exc_type, why),
#                 level=3,
#             )
#             self.failed.append(ext.name)

#     def add_multiarch_paths(self):
#         # Debian/Ubuntu multiarch support.
#         # https://wiki.ubuntu.com/MultiarchSpec
#         cc = sysconfig.get_config_var('CC')
#         tmpfile = os.path.join(self.build_temp, 'multiarch')
#         if not os.path.exists(self.build_temp):
#             os.makedirs(self.build_temp)
#         ret = run_command('%s -print-multiarch > %s 2> /dev/null' % (cc, tmpfile))
#         multiarch_path_component = ''
#         try:
#             if ret == 0:
#                 with open(tmpfile) as fp:
#                     multiarch_path_component = fp.readline().strip()
#         finally:
#             os.unlink(tmpfile)

#         if multiarch_path_component != '':
#             add_dir_to_list(self.compiler.library_dirs, '/usr/lib/' + multiarch_path_component)
#             add_dir_to_list(self.compiler.include_dirs, '/usr/include/' + multiarch_path_component)
#             return

#         if not find_executable('dpkg-architecture'):
#             return
#         opt = ''
#         if CROSS_COMPILING:
#             opt = '-t' + sysconfig.get_config_var('HOST_GNU_TYPE')
#         tmpfile = os.path.join(self.build_temp, 'multiarch')
#         if not os.path.exists(self.build_temp):
#             os.makedirs(self.build_temp)
#         ret = run_command(
#             'dpkg-architecture %s -qDEB_HOST_MULTIARCH > %s 2> /dev/null' % (opt, tmpfile)
#         )
#         try:
#             if ret == 0:
#                 with open(tmpfile) as fp:
#                     multiarch_path_component = fp.readline().strip()
#                 add_dir_to_list(self.compiler.library_dirs, '/usr/lib/' + multiarch_path_component)
#                 add_dir_to_list(
#                     self.compiler.include_dirs, '/usr/include/' + multiarch_path_component
#                 )
#         finally:
#             os.unlink(tmpfile)

#     def add_cross_compiling_paths(self):
#         cc = sysconfig.get_config_var('CC')
#         tmpfile = os.path.join(self.build_temp, 'ccpaths')
#         if not os.path.exists(self.build_temp):
#             os.makedirs(self.build_temp)
#         ret = run_command('%s -E -v - </dev/null 2>%s 1>/dev/null' % (cc, tmpfile))
#         is_gcc = False
#         is_clang = False
#         in_incdirs = False
#         try:
#             if ret == 0:
#                 with open(tmpfile) as fp:
#                     for line in fp.readlines():
#                         if line.startswith("gcc version"):
#                             is_gcc = True
#                         elif line.startswith("clang version"):
#                             is_clang = True
#                         elif line.startswith("#include <...>"):
#                             in_incdirs = True
#                         elif line.startswith("End of search list"):
#                             in_incdirs = False
#                         elif (is_gcc or is_clang) and line.startswith("LIBRARY_PATH"):
#                             for d in line.strip().split("=")[1].split(":"):
#                                 d = os.path.normpath(d)
#                                 if '/gcc/' not in d:
#                                     add_dir_to_list(self.compiler.library_dirs, d)
#                         elif (
#                             (is_gcc or is_clang)
#                             and in_incdirs
#                             and '/gcc/' not in line
#                             and '/clang/' not in line
#                         ):
#                             add_dir_to_list(self.compiler.include_dirs, line.strip())
#         finally:
#             os.unlink(tmpfile)

#     def add_ldflags_cppflags(self):
#         # Add paths specified in the environment variables LDFLAGS and
#         # CPPFLAGS for header and library files.
#         # We must get the values from the Makefile and not the environment
#         # directly since an inconsistently reproducible issue comes up where
#         # the environment variable is not set even though the value were passed
#         # into configure and stored in the Makefile (issue found on OS X 10.3).
#         for env_var, arg_name, dir_list in (
#             ('LDFLAGS', '-R', self.compiler.runtime_library_dirs),
#             ('LDFLAGS', '-L', self.compiler.library_dirs),
#             ('CPPFLAGS', '-I', self.compiler.include_dirs),
#         ):
#             env_val = sysconfig.get_config_var(env_var)
#             if env_val:
#                 parser = argparse.ArgumentParser()
#                 parser.add_argument(arg_name, dest="dirs", action="append")
#                 options, _ = parser.parse_known_args(env_val.split())
#                 if options.dirs:
#                     for directory in reversed(options.dirs):
#                         add_dir_to_list(dir_list, directory)

#     def configure_compiler(self):
#         # Ensure that /usr/local is always used, but the local build
#         # directories (i.e. '.' and 'Include') must be first.  See issue
#         # 10520.
#         if not CROSS_COMPILING:
#             add_dir_to_list(self.compiler.library_dirs, '/usr/local/lib')
#             add_dir_to_list(self.compiler.include_dirs, '/usr/local/include')
#         # only change this for cross builds for 3.3, issues on Mageia
#         if CROSS_COMPILING:
#             self.add_cross_compiling_paths()
#         self.add_multiarch_paths()
#         self.add_ldflags_cppflags()

#     def init_inc_lib_dirs(self):
#         if (
#             not CROSS_COMPILING
#             and os.path.normpath(sys.base_prefix) != '/usr'
#             and not sysconfig.get_config_var('PYTHONFRAMEWORK')
#         ):
#             # OSX note: Don't add LIBDIR and INCLUDEDIR to building a framework
#             # (PYTHONFRAMEWORK is set) to avoid # linking problems when
#             # building a framework with different architectures than
#             # the one that is currently installed (issue #7473)
#             add_dir_to_list(self.compiler.library_dirs, sysconfig.get_config_var("LIBDIR"))
#             add_dir_to_list(self.compiler.include_dirs, sysconfig.get_config_var("INCLUDEDIR"))

#         system_lib_dirs = ['/lib64', '/usr/lib64', '/lib', '/usr/lib']
#         system_include_dirs = ['/usr/include']
#         # lib_dirs and inc_dirs are used to search for files;
#         # if a file is found in one of those directories, it can
#         # be assumed that no additional -I,-L directives are needed.
#         if not CROSS_COMPILING:
#             self.lib_dirs = self.compiler.library_dirs + system_lib_dirs
#             self.inc_dirs = self.compiler.include_dirs + system_include_dirs
#         else:
#             # Add the sysroot paths. 'sysroot' is a compiler option used to
#             # set the logical path of the standard system headers and
#             # libraries.
#             self.lib_dirs = self.compiler.library_dirs + sysroot_paths(
#                 ('LDFLAGS', 'CC'), system_lib_dirs
#             )
#             self.inc_dirs = self.compiler.include_dirs + sysroot_paths(
#                 ('CPPFLAGS', 'CFLAGS', 'CC'), system_include_dirs
#             )

#         config_h = sysconfig.get_config_h_filename()
#         with open(config_h) as file:
#             self.config_h_vars = sysconfig.parse_config_h(file)

#         # OSF/1 and Unixware have some stuff in /usr/ccs/lib (like -ldb)
#         if HOST_PLATFORM in ['osf1', 'unixware7', 'openunix8']:
#             self.lib_dirs += ['/usr/ccs/lib']

#         # HP-UX11iv3 keeps files in lib/hpux folders.
#         if HOST_PLATFORM == 'hp-ux11':
#             self.lib_dirs += ['/usr/lib/hpux64', '/usr/lib/hpux32']

#         if MACOS:
#             # This should work on any unixy platform ;-)
#             # If the user has bothered specifying additional -I and -L flags
#             # in OPT and LDFLAGS we might as well use them here.
#             #
#             # NOTE: using shlex.split would technically be more correct, but
#             # also gives a bootstrap problem. Let's hope nobody uses
#             # directories with whitespace in the name to store libraries.
#             cflags, ldflags = sysconfig.get_config_vars('CFLAGS', 'LDFLAGS')
#             for item in cflags.split():
#                 if item.startswith('-I'):
#                     self.inc_dirs.append(item[2:])

#             for item in ldflags.split():
#                 if item.startswith('-L'):
#                     self.lib_dirs.append(item[2:])

#     def detect_simple_extensions(self):
#         #
#         # The following modules are all pretty straightforward, and compile
#         # on pretty much any POSIXish platform.
#         #

#         # array objects
#         self.add(Extension('array', ['arraymodule.c']))

#         # Context Variables
#         self.add(Extension('_contextvars', ['_contextvarsmodule.c']))

#         shared_math = 'Modules/_math.o'

#         # math library functions, e.g. sin()
#         self.add(
#             Extension(
#                 'math',
#                 ['mathmodule.c'],
#                 extra_compile_args=['-DPy_BUILD_CORE_MODULE'],
#                 extra_objects=[shared_math],
#                 depends=['_math.h', shared_math],
#                 libraries=['m'],
#             )
#         )

#         # complex math library functions
#         self.add(
#             Extension(
#                 'cmath',
#                 ['cmathmodule.c'],
#                 extra_compile_args=['-DPy_BUILD_CORE_MODULE'],
#                 extra_objects=[shared_math],
#                 depends=['_math.h', shared_math],
#                 libraries=['m'],
#             )
#         )

#         # time libraries: librt may be needed for clock_gettime()
#         time_libs = []
#         lib = sysconfig.get_config_var('TIMEMODULE_LIB')
#         if lib:
#             time_libs.append(lib)

#         # time operations and variables
#         self.add(Extension('time', ['timemodule.c'], libraries=time_libs))
#         # libm is needed by delta_new() that uses round() and by accum() that
#         # uses modf().
#         self.add(
#             Extension(
#                 '_datetime',
#                 ['_datetimemodule.c'],
#                 libraries=['m'],
#                 extra_compile_args=['-DPy_BUILD_CORE_MODULE'],
#             )
#         )
#         # zoneinfo module
#         self.add(Extension('_zoneinfo', ['_zoneinfo.c'])),
#         # random number generator implemented in C
#         self.add(
#             Extension(
#                 "_random", ["_randommodule.c"], extra_compile_args=['-DPy_BUILD_CORE_MODULE']
#             )
#         )
#         # bisect
#         self.add(Extension("_bisect", ["_bisectmodule.c"]))
#         # heapq
#         self.add(
#             Extension("_heapq", ["_heapqmodule.c"], extra_compile_args=['-DPy_BUILD_CORE_MODULE'])
#         )
#         # atexit
#         self.add(Extension("atexit", ["atexitmodule.c"]))
#         # _json speedups
#         self.add(Extension("_json", ["_json.c"], extra_compile_args=['-DPy_BUILD_CORE_MODULE']))

#         # profiler (_lsprof is for cProfile.py)
#         self.add(Extension('_lsprof', ['_lsprof.c', 'rotatingtree.c']))
#         # static Unicode character database
#         self.add(
#             Extension(
#                 'unicodedata', ['unicodedata.c'], depends=['unicodedata_db.h', 'unicodename_db.h']
#             )
#         )
#         # _opcode module
#         self.add(Extension('_opcode', ['_opcode.c']))
#         # asyncio speedups
#         self.add(
#             Extension(
#                 "_asyncio", ["_asynciomodule.c"], extra_compile_args=['-DPy_BUILD_CORE_MODULE']
#             )
#         )
#         # _abc speedups
#         self.add(Extension("_abc", ["_abc.c"]))
#         # _queue module
#         self.add(Extension("_queue", ["_queuemodule.c"]))
#         # _statistics module
#         self.add(Extension("_statistics", ["_statisticsmodule.c"]))

#         # Modules with some UNIX dependencies -- on by default:
#         # (If you have a really backward UNIX, select and socket may not be
#         # supported...)

#         # fcntl(2) and ioctl(2)
#         libs = []
#         if self.config_h_vars.get('FLOCK_NEEDS_LIBBSD', False):
#             # May be necessary on AIX for flock function
#             libs = ['bsd']
#         self.add(Extension('fcntl', ['fcntlmodule.c'], libraries=libs))

#         # select(2); not on ancient System V
#         self.add(Extension('select', ['selectmodule.c']))

#         # Memory-mapped files (also works on Win32).
#         self.add(Extension('mmap', ['mmapmodule.c']))

#         # Lance Ellinghaus's syslog module
#         # syslog daemon interface
#         self.add(Extension('syslog', ['syslogmodule.c']))

#         # Python interface to subinterpreter C-API.
#         self.add(Extension('_xxsubinterpreters', ['_xxsubinterpretersmodule.c']))

#         #
#         # Here ends the simple stuff.  From here on, modules need certain
#         # libraries, are platform-specific, or present other surprises.
#         #

#         # Multimedia modules
#         # These don't work for 64-bit platforms!!!
#         # These represent audio samples or images as strings:
#         #
#         # Operations on audio samples
#         # According to #993173, this one should actually work fine on
#         # 64-bit platforms.
#         #
#         # audioop needs libm for floor() in multiple functions.
#         self.add(Extension('audioop', ['audioop.c'], libraries=['m']))

#     def detect_test_extensions(self):
#         # Python C API test module
#         self.add(Extension('_testcapi', ['_testcapimodule.c'], depends=['testcapi_long.h']))

#         # Python Internal C API test module
#         self.add(
#             Extension(
#                 '_testinternalcapi',
#                 ['_testinternalcapi.c'],
#                 extra_compile_args=['-DPy_BUILD_CORE_MODULE'],
#             )
#         )

#         # Python PEP-3118 (buffer protocol) test module
#         self.add(Extension('_testbuffer', ['_testbuffer.c']))

#         # Test loading multiple modules from one compiled file (http://bugs.python.org/issue16421)
#         self.add(Extension('_testimportmultiple', ['_testimportmultiple.c']))

#         # Test multi-phase extension module init (PEP 489)
#         self.add(Extension('_testmultiphase', ['_testmultiphase.c']))

#     def detect_crypt(self):
#         # crypt module.
#         if VXWORKS:
#             # bpo-31904: crypt() function is not provided by VxWorks.
#             # DES_crypt() OpenSSL provides is too weak to implement
#             # the encryption.
#             return

#         if self.compiler.find_library_file(self.lib_dirs, 'crypt'):
#             libs = ['crypt']
#         else:
#             libs = []

#         self.add(Extension('_crypt', ['_cryptmodule.c'], libraries=libs))

#     def detect_dbm_gdbm(self):
#         # Modules that provide persistent dictionary-like semantics.  You will
#         # probably want to arrange for at least one of them to be available on
#         # your machine, though none are defined by default because of library
#         # dependencies.  The Python module dbm/__init__.py provides an
#         # implementation independent wrapper for these; dbm/dumb.py provides
#         # similar functionality (but slower of course) implemented in Python.

#         # Sleepycat^WOracle Berkeley DB interface.
#         #  http://www.oracle.com/database/berkeley-db/db/index.html
#         #
#         # This requires the Sleepycat^WOracle DB code. The supported versions
#         # are set below.  Visit the URL above to download
#         # a release.  Most open source OSes come with one or more
#         # versions of BerkeleyDB already installed.

#         max_db_ver = (5, 3)
#         min_db_ver = (3, 3)
#         db_setup_debug = False  # verbose debug prints from this script?

#         def allow_db_ver(db_ver):
#             """Returns a boolean if the given BerkeleyDB version is acceptable.

#             Args:
#               db_ver: A tuple of the version to verify.
#             """
#             if not (min_db_ver <= db_ver <= max_db_ver):
#                 return False
#             return True

#         def gen_db_minor_ver_nums(major):
#             if major == 4:
#                 for x in range(max_db_ver[1] + 1):
#                     if allow_db_ver((4, x)):
#                         yield x
#             elif major == 3:
#                 for x in (3,):
#                     if allow_db_ver((3, x)):
#                         yield x
#             else:
#                 raise ValueError("unknown major BerkeleyDB version", major)

#         # construct a list of paths to look for the header file in on
#         # top of the normal inc_dirs.
#         db_inc_paths = [
#             '/usr/include/db4',
#             '/usr/local/include/db4',
#             '/opt/sfw/include/db4',
#             '/usr/include/db3',
#             '/usr/local/include/db3',
#             '/opt/sfw/include/db3',
#             # Fink defaults (http://fink.sourceforge.net/)
#             '/sw/include/db4',
#             '/sw/include/db3',
#         ]
#         # 4.x minor number specific paths
#         for x in gen_db_minor_ver_nums(4):
#             db_inc_paths.append('/usr/include/db4%d' % x)
#             db_inc_paths.append('/usr/include/db4.%d' % x)
#             db_inc_paths.append('/usr/local/BerkeleyDB.4.%d/include' % x)
#             db_inc_paths.append('/usr/local/include/db4%d' % x)
#             db_inc_paths.append('/pkg/db-4.%d/include' % x)
#             db_inc_paths.append('/opt/db-4.%d/include' % x)
#             # MacPorts default (http://www.macports.org/)
#             db_inc_paths.append('/opt/local/include/db4%d' % x)
#         # 3.x minor number specific paths
#         for x in gen_db_minor_ver_nums(3):
#             db_inc_paths.append('/usr/include/db3%d' % x)
#             db_inc_paths.append('/usr/local/BerkeleyDB.3.%d/include' % x)
#             db_inc_paths.append('/usr/local/include/db3%d' % x)
#             db_inc_paths.append('/pkg/db-3.%d/include' % x)
#             db_inc_paths.append('/opt/db-3.%d/include' % x)

#         if CROSS_COMPILING:
#             db_inc_paths = []

#         # Add some common subdirectories for Sleepycat DB to the list,
#         # based on the standard include directories. This way DB3/4 gets
#         # picked up when it is installed in a non-standard prefix and
#         # the user has added that prefix into inc_dirs.
#         std_variants = []
#         for dn in self.inc_dirs:
#             std_variants.append(os.path.join(dn, 'db3'))
#             std_variants.append(os.path.join(dn, 'db4'))
#             for x in gen_db_minor_ver_nums(4):
#                 std_variants.append(os.path.join(dn, "db4%d" % x))
#                 std_variants.append(os.path.join(dn, "db4.%d" % x))
#             for x in gen_db_minor_ver_nums(3):
#                 std_variants.append(os.path.join(dn, "db3%d" % x))
#                 std_variants.append(os.path.join(dn, "db3.%d" % x))

#         db_inc_paths = std_variants + db_inc_paths
#         db_inc_paths = [p for p in db_inc_paths if os.path.exists(p)]

#         db_ver_inc_map = {}

#         if MACOS:
#             sysroot = macosx_sdk_root()

#         class db_found(Exception):
#             pass

#         try:
#             # See whether there is a Sleepycat header in the standard
#             # search path.
#             for d in self.inc_dirs + db_inc_paths:
#                 f = os.path.join(d, "db.h")
#                 if MACOS and is_macosx_sdk_path(d):
#                     f = os.path.join(sysroot, d[1:], "db.h")

#                 if db_setup_debug:
#                     print("db: looking for db.h in", f)
#                 if os.path.exists(f):
#                     with open(f, 'rb') as file:
#                         f = file.read()
#                     m = re.search(br"#define\WDB_VERSION_MAJOR\W(\d+)", f)
#                     if m:
#                         db_major = int(m.group(1))
#                         m = re.search(br"#define\WDB_VERSION_MINOR\W(\d+)", f)
#                         db_minor = int(m.group(1))
#                         db_ver = (db_major, db_minor)

#                         # Avoid 4.6 prior to 4.6.21 due to a BerkeleyDB bug
#                         if db_ver == (4, 6):
#                             m = re.search(br"#define\WDB_VERSION_PATCH\W(\d+)", f)
#                             db_patch = int(m.group(1))
#                             if db_patch < 21:
#                                 print(
#                                     "db.h:",
#                                     db_ver,
#                                     "patch",
#                                     db_patch,
#                                     "being ignored (4.6.x must be >= 4.6.21)",
#                                 )
#                                 continue

#                         if (db_ver not in db_ver_inc_map) and allow_db_ver(db_ver):
#                             # save the include directory with the db.h version
#                             # (first occurrence only)
#                             db_ver_inc_map[db_ver] = d
#                             if db_setup_debug:
#                                 print("db.h: found", db_ver, "in", d)
#                         else:
#                             # we already found a header for this library version
#                             if db_setup_debug:
#                                 print("db.h: ignoring", d)
#                     else:
#                         # ignore this header, it didn't contain a version number
#                         if db_setup_debug:
#                             print("db.h: no version number version in", d)

#             db_found_vers = list(db_ver_inc_map.keys())
#             db_found_vers.sort()

#             while db_found_vers:
#                 db_ver = db_found_vers.pop()
#                 db_incdir = db_ver_inc_map[db_ver]

#                 # check lib directories parallel to the location of the header
#                 db_dirs_to_check = [
#                     db_incdir.replace("include", 'lib64'),
#                     db_incdir.replace("include", 'lib'),
#                 ]

#                 if not MACOS:
#                     db_dirs_to_check = list(filter(os.path.isdir, db_dirs_to_check))

#                 else:
#                     # Same as other branch, but takes OSX SDK into account
#                     tmp = []
#                     for dn in db_dirs_to_check:
#                         if is_macosx_sdk_path(dn):
#                             if os.path.isdir(os.path.join(sysroot, dn[1:])):
#                                 tmp.append(dn)
#                         else:
#                             if os.path.isdir(dn):
#                                 tmp.append(dn)
#                     db_dirs_to_check = tmp

#                     db_dirs_to_check = tmp

#                 # Look for a version specific db-X.Y before an ambiguous dbX
#                 # XXX should we -ever- look for a dbX name?  Do any
#                 # systems really not name their library by version and
#                 # symlink to more general names?
#                 for dblib in (('db-%d.%d' % db_ver), ('db%d%d' % db_ver), ('db%d' % db_ver[0])):
#                     dblib_file = self.compiler.find_library_file(
#                         db_dirs_to_check + self.lib_dirs, dblib
#                     )
#                     if dblib_file:
#                         dblib_dir = [os.path.abspath(os.path.dirname(dblib_file))]
#                         raise db_found
#                     else:
#                         if db_setup_debug:
#                             print("db lib: ", dblib, "not found")

#         except db_found:
#             if db_setup_debug:
#                 print("bsddb using BerkeleyDB lib:", db_ver, dblib)
#                 print("bsddb lib dir:", dblib_dir, " inc dir:", db_incdir)
#             dblibs = [dblib]
#             # Only add the found library and include directories if they aren't
#             # already being searched. This avoids an explicit runtime library
#             # dependency.
#             if db_incdir in self.inc_dirs:
#                 db_incs = None
#             else:
#                 db_incs = [db_incdir]
#             if dblib_dir[0] in self.lib_dirs:
#                 dblib_dir = None
#         else:
#             if db_setup_debug:
#                 print("db: no appropriate library found")
#             db_incs = None
#             dblibs = []
#             dblib_dir = None

#         dbm_setup_debug = False  # verbose debug prints from this script?
#         dbm_order = ['gdbm']
#         # The standard Unix dbm module:
#         if not CYGWIN:
#             config_args = [
#                 arg.strip("'") for arg in sysconfig.get_config_var("CONFIG_ARGS").split()
#             ]
#             dbm_args = [arg for arg in config_args if arg.startswith('--with-dbmliborder=')]
#             if dbm_args:
#                 dbm_order = [arg.split('=')[-1] for arg in dbm_args][-1].split(":")
#             else:
#                 dbm_order = "ndbm:gdbm:bdb".split(":")
#             dbmext = None
#             for cand in dbm_order:
#                 if cand == "ndbm":
#                     if find_file("ndbm.h", self.inc_dirs, []) is not None:
#                         # Some systems have -lndbm, others have -lgdbm_compat,
#                         # others don't have either
#                         if self.compiler.find_library_file(self.lib_dirs, 'ndbm'):
#                             ndbm_libs = ['ndbm']
#                         elif self.compiler.find_library_file(self.lib_dirs, 'gdbm_compat'):
#                             ndbm_libs = ['gdbm_compat']
#                         else:
#                             ndbm_libs = []
#                         if dbm_setup_debug:
#                             print("building dbm using ndbm")
#                         dbmext = Extension(
#                             '_dbm',
#                             ['_dbmmodule.c'],
#                             define_macros=[('HAVE_NDBM_H', None),],
#                             libraries=ndbm_libs,
#                         )
#                         break

#                 elif cand == "gdbm":
#                     if self.compiler.find_library_file(self.lib_dirs, 'gdbm'):
#                         gdbm_libs = ['gdbm']
#                         if self.compiler.find_library_file(self.lib_dirs, 'gdbm_compat'):
#                             gdbm_libs.append('gdbm_compat')
#                         if find_file("gdbm/ndbm.h", self.inc_dirs, []) is not None:
#                             if dbm_setup_debug:
#                                 print("building dbm using gdbm")
#                             dbmext = Extension(
#                                 '_dbm',
#                                 ['_dbmmodule.c'],
#                                 define_macros=[('HAVE_GDBM_NDBM_H', None),],
#                                 libraries=gdbm_libs,
#                             )
#                             break
#                         if find_file("gdbm-ndbm.h", self.inc_dirs, []) is not None:
#                             if dbm_setup_debug:
#                                 print("building dbm using gdbm")
#                             dbmext = Extension(
#                                 '_dbm',
#                                 ['_dbmmodule.c'],
#                                 define_macros=[('HAVE_GDBM_DASH_NDBM_H', None),],
#                                 libraries=gdbm_libs,
#                             )
#                             break
#                 elif cand == "bdb":
#                     if dblibs:
#                         if dbm_setup_debug:
#                             print("building dbm using bdb")
#                         dbmext = Extension(
#                             '_dbm',
#                             ['_dbmmodule.c'],
#                             library_dirs=dblib_dir,
#                             runtime_library_dirs=dblib_dir,
#                             include_dirs=db_incs,
#                             define_macros=[('HAVE_BERKDB_H', None), ('DB_DBM_HSEARCH', None),],
#                             libraries=dblibs,
#                         )
#                         break
#             if dbmext is not None:
#                 self.add(dbmext)
#             else:
#                 self.missing.append('_dbm')

#         # Anthony Baxter's gdbm module.  GNU dbm(3) will require -lgdbm:
#         if 'gdbm' in dbm_order and self.compiler.find_library_file(self.lib_dirs, 'gdbm'):
#             self.add(Extension('_gdbm', ['_gdbmmodule.c'], libraries=['gdbm']))
#         else:
#             self.missing.append('_gdbm')

#     def detect_platform_specific_exts(self):
#         # Unix-only modules
#         if not MS_WINDOWS:
#             if not VXWORKS:
#                 # Steen Lumholt's termios module
#                 self.add(Extension('termios', ['termios.c']))
#                 # Jeremy Hylton's rlimit interface
#             self.add(Extension('resource', ['resource.c']))
#         else:
#             self.missing.extend(['resource', 'termios'])

#     def detect_compress_exts(self):

#         # Helper module for various ascii-encoders.  Uses zlib for an optimized
#         # crc32 if we have it.  Otherwise binascii uses its own.

#         self.add(
#             Extension(
#                 'binascii',
#                 ['binascii.c'],
#                 extra_compile_args=[],
#                 libraries=[],
#                 extra_link_args=[],
#             )
#         )

#     def detect_multibytecodecs(self):
#         # Hye-Shik Chang's CJKCodecs modules.
#         self.add(Extension('_multibytecodec', ['cjkcodecs/multibytecodec.c']))
#         for loc in ('kr', 'jp', 'cn', 'tw', 'hk', 'iso2022'):
#             self.add(Extension('_codecs_%s' % loc, ['cjkcodecs/_codecs_%s.c' % loc]))

#     def detect_modules(self):
#         self.configure_compiler()
#         self.init_inc_lib_dirs()

#         self.detect_simple_extensions()
#         if TEST_EXTENSIONS:
#             self.detect_test_extensions()
#         self.detect_crypt()
#         self.detect_hash_builtins()
#         self.detect_dbm_gdbm()
#         self.detect_platform_specific_exts()
#         self.detect_nis()
#         self.detect_compress_exts()
#         self.detect_multibytecodecs()
#         self.detect_decimal()
#         self.detect_ctypes()

#         ##         # Uncomment these lines if you want to play with xxmodule.c
#         ##         self.add(Extension('xx', ['xxmodule.c']))

#         if 'd' not in sysconfig.get_config_var('ABIFLAGS'):
#             self.add(
#                 Extension(
#                     'xxlimited', ['xxlimited.c'], define_macros=[('Py_LIMITED_API', '0x03050000')]
#                 )
#             )

#     def configure_ctypes_darwin(self, ext):
#         # Darwin (OS X) uses preconfigured files, in
#         # the Modules/_ctypes/libffi_osx directory.
#         ffi_srcdir = os.path.abspath(os.path.join(self.srcdir, 'Modules', '_ctypes', 'libffi_osx'))
#         sources = [
#             os.path.join(ffi_srcdir, p)
#             for p in [
#                 'ffi.c',
#                 'x86/darwin64.S',
#                 'x86/x86-darwin.S',
#                 'x86/x86-ffi_darwin.c',
#                 'x86/x86-ffi64.c',
#                 'powerpc/ppc-darwin.S',
#                 'powerpc/ppc-darwin_closure.S',
#                 'powerpc/ppc-ffi_darwin.c',
#                 'powerpc/ppc64-darwin_closure.S',
#             ]
#         ]

#         # Add .S (preprocessed assembly) to C compiler source extensions.
#         self.compiler.src_extensions.append('.S')

#         include_dirs = [os.path.join(ffi_srcdir, 'include'), os.path.join(ffi_srcdir, 'powerpc')]
#         ext.include_dirs.extend(include_dirs)
#         ext.sources.extend(sources)
#         return True

#     def configure_ctypes(self, ext):
#         if not self.use_system_libffi:
#             if MACOS:
#                 return self.configure_ctypes_darwin(ext)
#             print('INFO: Could not locate ffi libs and/or headers')
#             return False
#         return True

#     def detect_ctypes(self):
#         # Thomas Heller's _ctypes module
#         self.use_system_libffi = False
#         include_dirs = []
#         extra_compile_args = ['-DPy_BUILD_CORE_MODULE']
#         extra_link_args = []
#         sources = [
#             '_ctypes/_ctypes.c',
#             '_ctypes/callbacks.c',
#             '_ctypes/callproc.c',
#             '_ctypes/stgdict.c',
#             '_ctypes/cfield.c',
#         ]
#         depends = ['_ctypes/ctypes.h']

#         if MACOS:
#             sources.append('_ctypes/malloc_closure.c')
#             sources.append('_ctypes/darwin/dlfcn_simple.c')
#             extra_compile_args.append('-DMACOSX')
#             include_dirs.append('_ctypes/darwin')
#             # XXX Is this still needed?
#             # extra_link_args.extend(['-read_only_relocs', 'warning'])

#         elif HOST_PLATFORM == 'sunos5':
#             # XXX This shouldn't be necessary; it appears that some
#             # of the assembler code is non-PIC (i.e. it has relocations
#             # when it shouldn't. The proper fix would be to rewrite
#             # the assembler code to be PIC.
#             # This only works with GCC; the Sun compiler likely refuses
#             # this option. If you want to compile ctypes with the Sun
#             # compiler, please research a proper solution, instead of
#             # finding some -z option for the Sun compiler.
#             extra_link_args.append('-mimpure-text')

#         elif HOST_PLATFORM.startswith('hp-ux'):
#             extra_link_args.append('-fPIC')

#         ext = Extension(
#             '_ctypes',
#             include_dirs=include_dirs,
#             extra_compile_args=extra_compile_args,
#             extra_link_args=extra_link_args,
#             libraries=[],
#             sources=sources,
#             depends=depends,
#         )
#         self.add(ext)
#         if TEST_EXTENSIONS:
#             # function my_sqrt() needs libm for sqrt()
#             self.add(
#                 Extension('_ctypes_test', sources=['_ctypes/_ctypes_test.c'], libraries=['m'])
#             )

#         ffi_inc_dirs = self.inc_dirs.copy()
#         if MACOS:
#             if '--with-system-ffi' not in sysconfig.get_config_var("CONFIG_ARGS"):
#                 return
#             # OS X 10.5 comes with libffi.dylib; the include files are
#             # in /usr/include/ffi
#             ffi_inc_dirs.append('/usr/include/ffi')

#         ffi_inc = [sysconfig.get_config_var("LIBFFI_INCLUDEDIR")]
#         if not ffi_inc or ffi_inc[0] == '':
#             ffi_inc = find_file('ffi.h', [], ffi_inc_dirs)
#         if ffi_inc is not None:
#             ffi_h = ffi_inc[0] + '/ffi.h'
#             if not os.path.exists(ffi_h):
#                 ffi_inc = None
#                 print('Header file {} does not exist'.format(ffi_h))
#         ffi_lib = None
#         if ffi_inc is not None:
#             for lib_name in ('ffi', 'ffi_pic'):
#                 if self.compiler.find_library_file(self.lib_dirs, lib_name):
#                     ffi_lib = lib_name
#                     break

#         if ffi_inc and ffi_lib:
#             ext.include_dirs.extend(ffi_inc)
#             ext.libraries.append(ffi_lib)
#             self.use_system_libffi = True

#         if sysconfig.get_config_var('HAVE_LIBDL'):
#             # for dlopen, see bpo-32647
#             ext.libraries.append('dl')

#     def detect_decimal(self):
#         # Stefan Krah's _decimal module
#         extra_compile_args = []
#         undef_macros = []
#         if '--with-system-libmpdec' in sysconfig.get_config_var("CONFIG_ARGS"):
#             include_dirs = []
#             libraries = [':libmpdec.so.2']
#             sources = ['_decimal/_decimal.c']
#             depends = ['_decimal/docstrings.h']
#         else:
#             include_dirs = [
#                 os.path.abspath(os.path.join(self.srcdir, 'Modules', '_decimal', 'libmpdec'))
#             ]
#             libraries = ['m']
#             sources = [
#                 '_decimal/_decimal.c',
#                 '_decimal/libmpdec/basearith.c',
#                 '_decimal/libmpdec/constants.c',
#                 '_decimal/libmpdec/context.c',
#                 '_decimal/libmpdec/convolute.c',
#                 '_decimal/libmpdec/crt.c',
#                 '_decimal/libmpdec/difradix2.c',
#                 '_decimal/libmpdec/fnt.c',
#                 '_decimal/libmpdec/fourstep.c',
#                 '_decimal/libmpdec/io.c',
#                 '_decimal/libmpdec/mpalloc.c',
#                 '_decimal/libmpdec/mpdecimal.c',
#                 '_decimal/libmpdec/numbertheory.c',
#                 '_decimal/libmpdec/sixstep.c',
#                 '_decimal/libmpdec/transpose.c',
#             ]
#             depends = [
#                 '_decimal/docstrings.h',
#                 '_decimal/libmpdec/basearith.h',
#                 '_decimal/libmpdec/bits.h',
#                 '_decimal/libmpdec/constants.h',
#                 '_decimal/libmpdec/convolute.h',
#                 '_decimal/libmpdec/crt.h',
#                 '_decimal/libmpdec/difradix2.h',
#                 '_decimal/libmpdec/fnt.h',
#                 '_decimal/libmpdec/fourstep.h',
#                 '_decimal/libmpdec/io.h',
#                 '_decimal/libmpdec/mpalloc.h',
#                 '_decimal/libmpdec/mpdecimal.h',
#                 '_decimal/libmpdec/numbertheory.h',
#                 '_decimal/libmpdec/sixstep.h',
#                 '_decimal/libmpdec/transpose.h',
#                 '_decimal/libmpdec/typearith.h',
#                 '_decimal/libmpdec/umodarith.h',
#             ]

#         config = {
#             'x64': [('CONFIG_64', '1'), ('ASM', '1')],
#             'uint128': [('CONFIG_64', '1'), ('ANSI', '1'), ('HAVE_UINT128_T', '1')],
#             'ansi64': [('CONFIG_64', '1'), ('ANSI', '1')],
#             'ppro': [('CONFIG_32', '1'), ('PPRO', '1'), ('ASM', '1')],
#             'ansi32': [('CONFIG_32', '1'), ('ANSI', '1')],
#             'ansi-legacy': [('CONFIG_32', '1'), ('ANSI', '1'), ('LEGACY_COMPILER', '1')],
#             'universal': [('UNIVERSAL', '1')],
#         }

#         cc = sysconfig.get_config_var('CC')
#         sizeof_size_t = sysconfig.get_config_var('SIZEOF_SIZE_T')
#         machine = os.environ.get('PYTHON_DECIMAL_WITH_MACHINE')

#         if machine:
#             # Override automatic configuration to facilitate testing.
#             define_macros = config[machine]
#         elif MACOS:
#             # Universal here means: build with the same options Python
#             # was built with.
#             define_macros = config['universal']
#         elif sizeof_size_t == 8:
#             if sysconfig.get_config_var('HAVE_GCC_ASM_FOR_X64'):
#                 define_macros = config['x64']
#             elif sysconfig.get_config_var('HAVE_GCC_UINT128_T'):
#                 define_macros = config['uint128']
#             else:
#                 define_macros = config['ansi64']
#         elif sizeof_size_t == 4:
#             ppro = sysconfig.get_config_var('HAVE_GCC_ASM_FOR_X87')
#             if ppro and ('gcc' in cc or 'clang' in cc) and not 'sunos' in HOST_PLATFORM:
#                 # solaris: problems with register allocation.
#                 # icc >= 11.0 works as well.
#                 define_macros = config['ppro']
#                 extra_compile_args.append('-Wno-unknown-pragmas')
#             else:
#                 define_macros = config['ansi32']
#         else:
#             raise DistutilsError("_decimal: unsupported architecture")

#         # Workarounds for toolchain bugs:
#         if sysconfig.get_config_var('HAVE_IPA_PURE_CONST_BUG'):
#             # Some versions of gcc miscompile inline asm:
#             # http://gcc.gnu.org/bugzilla/show_bug.cgi?id=46491
#             # http://gcc.gnu.org/ml/gcc/2010-11/msg00366.html
#             extra_compile_args.append('-fno-ipa-pure-const')
#         if sysconfig.get_config_var('HAVE_GLIBC_MEMMOVE_BUG'):
#             # _FORTIFY_SOURCE wrappers for memmove and bcopy are incorrect:
#             # http://sourceware.org/ml/libc-alpha/2010-12/msg00009.html
#             undef_macros.append('_FORTIFY_SOURCE')

#         # Uncomment for extra functionality:
#         # define_macros.append(('EXTRA_FUNCTIONALITY', 1))
#         self.add(
#             Extension(
#                 '_decimal',
#                 include_dirs=include_dirs,
#                 libraries=libraries,
#                 define_macros=define_macros,
#                 undef_macros=undef_macros,
#                 extra_compile_args=extra_compile_args,
#                 sources=sources,
#                 depends=depends,
#             )
#         )

#     def detect_hash_builtins(self):
#         # By default we always compile these even when OpenSSL is available
#         # (issue #14693). It's harmless and the object code is tiny
#         # (40-50 KiB per module, only loaded when actually used).  Modules can
#         # be disabled via the --with-builtin-hashlib-hashes configure flag.
#         supported = {}

#         configured = sysconfig.get_config_var("PY_BUILTIN_HASHLIB_HASHES")

#     def detect_nis(self):
#         if MS_WINDOWS or CYGWIN or HOST_PLATFORM == 'qnx6':
#             self.missing.append('nis')
#             return

#         libs = []
#         library_dirs = []
#         includes_dirs = []

#         # bpo-32521: glibc has deprecated Sun RPC for some time. Fedora 28
#         # moved headers and libraries to libtirpc and libnsl. The headers
#         # are in tircp and nsl sub directories.
#         rpcsvc_inc = find_file(
#             'rpcsvc/yp_prot.h',
#             self.inc_dirs,
#             [os.path.join(inc_dir, 'nsl') for inc_dir in self.inc_dirs],
#         )
#         rpc_inc = find_file(
#             'rpc/rpc.h',
#             self.inc_dirs,
#             [os.path.join(inc_dir, 'tirpc') for inc_dir in self.inc_dirs],
#         )
#         if rpcsvc_inc is None or rpc_inc is None:
#             # not found
#             self.missing.append('nis')
#             return
#         includes_dirs.extend(rpcsvc_inc)
#         includes_dirs.extend(rpc_inc)

#         if self.compiler.find_library_file(self.lib_dirs, 'nsl'):
#             libs.append('nsl')
#         else:
#             # libnsl-devel: check for libnsl in nsl/ subdirectory
#             nsl_dirs = [os.path.join(lib_dir, 'nsl') for lib_dir in self.lib_dirs]
#             libnsl = self.compiler.find_library_file(nsl_dirs, 'nsl')
#             if libnsl is not None:
#                 library_dirs.append(os.path.dirname(libnsl))
#                 libs.append('nsl')

#         if self.compiler.find_library_file(self.lib_dirs, 'tirpc'):
#             libs.append('tirpc')

#         self.add(
#             Extension(
#                 'nis',
#                 ['nismodule.c'],
#                 libraries=libs,
#                 library_dirs=library_dirs,
#                 include_dirs=includes_dirs,
#             )
#         )


# class PyBuildInstall(install):
#     # Suppress the warning about installation into the lib_dynload
#     # directory, which is not in sys.path when running Python during
#     # installation:
#     def initialize_options(self):
#         install.initialize_options(self)
#         self.warn_dir = 0

#     # Customize subcommands to not install an egg-info file for Python
#     sub_commands = [
#         ('install_lib', install.has_lib),
#         ('install_headers', install.has_headers),
#         ('install_scripts', install.has_scripts),
#         ('install_data', install.has_data),
#     ]


# class PyBuildInstallLib(install_lib):
#     # Do exactly what install_lib does but make sure correct access modes get
#     # set on installed directories and files. All installed files with get
#     # mode 644 unless they are a shared library in which case they will get
#     # mode 755. All installed directories will get mode 755.

#     # this is works for EXT_SUFFIX too, which ends with SHLIB_SUFFIX
#     shlib_suffix = sysconfig.get_config_var("SHLIB_SUFFIX")

#     def install(self):
#         outfiles = install_lib.install(self)
#         self.set_file_modes(outfiles, 0o644, 0o755)
#         self.set_dir_modes(self.install_dir, 0o755)
#         return outfiles

#     def set_file_modes(self, files, defaultMode, sharedLibMode):
#         if not files:
#             return

#         for filename in files:
#             if os.path.islink(filename):
#                 continue
#             mode = defaultMode
#             if filename.endswith(self.shlib_suffix):
#                 mode = sharedLibMode
#             log.info("changing mode of %s to %o", filename, mode)
#             if not self.dry_run:
#                 os.chmod(filename, mode)

#     def set_dir_modes(self, dirname, mode):
#         for dirpath, dirnames, fnames in os.walk(dirname):
#             if os.path.islink(dirpath):
#                 continue
#             log.info("changing mode of %s to %o", dirpath, mode)
#             if not self.dry_run:
#                 os.chmod(dirpath, mode)


# class PyBuildScripts(build_scripts):
#     def copy_scripts(self):
#         outfiles, updated_files = build_scripts.copy_scripts(self)
#         fullversion = '-{0[0]}.{0[1]}'.format(sys.version_info)
#         minoronly = '.{0[1]}'.format(sys.version_info)
#         newoutfiles = []
#         newupdated_files = []
#         for filename in outfiles:
#             if filename.endswith('2to3'):
#                 newfilename = filename + fullversion
#             else:
#                 newfilename = filename + minoronly
#             log.info('renaming %s to %s', filename, newfilename)
#             os.rename(filename, newfilename)
#             newoutfiles.append(newfilename)
#             if filename in updated_files:
#                 newupdated_files.append(newfilename)
#         return newoutfiles, newupdated_files


# def main():
#     set_compiler_flags('CFLAGS', 'PY_CFLAGS_NODIST')
#     set_compiler_flags('LDFLAGS', 'PY_LDFLAGS_NODIST')

#     class DummyProcess:
#         """Hack for parallel build"""

#         ProcessPoolExecutor = None

#     sys.modules['concurrent.futures.process'] = DummyProcess
#     validate_tzpath()

#     # turn off warnings when deprecated modules are imported
#     import warnings

#     warnings.filterwarnings("ignore", category=DeprecationWarning)
#     setup(  # PyPI Metadata (PEP 301)
#         name="Python",
#         version=sys.version.split()[0],
#         url="http://www.python.org/%d.%d" % sys.version_info[:2],
#         maintainer="Guido van Rossum and the Python community",
#         maintainer_email="python-dev@python.org",
#         description="A high-level object-oriented programming language",
#         long_description=SUMMARY.strip(),
#         license="PSF license",
#         classifiers=[x for x in CLASSIFIERS.split("\n") if x],
#         platforms=["Many"],
#         # Build info
#         cmdclass={
#             # 'build_ext': PyBuildExt,
#             # 'build_scripts': PyBuildScripts,
#             # 'install': PyBuildInstall,
#             # 'install_lib': PyBuildInstallLib,
#         },
#         # The struct module is defined here, because build_ext won't be
#         # called unless there's at least one extension module defined.
#         ext_modules=[Extension('_struct', ['_struct.c'])],
#         # If you change the scripts installed here, you also need to
#         # check the PyBuildScripts command above, and change the links
#         # created by the bininstall target in Makefile.pre.in
#         scripts=[],
#     )


# # --install-platlib
# if __name__ == '__main__':
#     main()
