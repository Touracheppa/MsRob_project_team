/* SPDX-License-Identifier: Apache-2.0
 * Restrict Gazebo's EGL device discovery to Mesa software devices.
 * Intercept both direct calls and lookup through eglGetProcAddress.
 */
#define _GNU_SOURCE
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <dlfcn.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>

static pthread_once_t egl_once = PTHREAD_ONCE_INIT;
static PFNEGLGETPROCADDRESSPROC real_lookup;

static void load_egl(void)
{
  /* Ogre loads EGL with local visibility: RTLD_NEXT alone may not see it. */
  void *handle = dlopen("libEGL.so.1", RTLD_LAZY | RTLD_LOCAL);
  if (handle) real_lookup = (PFNEGLGETPROCADDRESSPROC)dlsym(handle, "eglGetProcAddress");
  /* Keep the handle alive for the lifetime of the preloaded library. */
}

static int has_extension(const char *extensions, const char *name)
{
  if (!extensions) return 0;
  size_t length = strlen(name);
  const char *position = extensions;
  while ((position = strstr(position, name))) {
    if ((position == extensions || position[-1] == ' ') &&
        (position[length] == '\0' || position[length] == ' ')) return 1;
    position += length;
  }
  return 0;
}

EGLBoolean EGLAPIENTRY eglQueryDevicesEXT(EGLint max_devices,
                                        EGLDeviceEXT *devices,
                                        EGLint *num_devices)
{
  pthread_once(&egl_once, load_egl);
  PFNEGLGETPROCADDRESSPROC lookup = real_lookup;
  if (!lookup || !num_devices || max_devices < 0) return EGL_FALSE;
  PFNEGLQUERYDEVICESEXTPROC query =
    (PFNEGLQUERYDEVICESEXTPROC)lookup("eglQueryDevicesEXT");
  PFNEGLQUERYDEVICESTRINGEXTPROC extensions =
    (PFNEGLQUERYDEVICESTRINGEXTPROC)lookup("eglQueryDeviceStringEXT");
  EGLint total = 0;
  if (!query || !extensions || !query(0, NULL, &total)) return EGL_FALSE;
  *num_devices = 0;
  if (total == 0) return EGL_TRUE;
  EGLDeviceEXT *all = calloc((size_t)total, sizeof(*all));
  if (!all) return EGL_FALSE;
  if (!query(total, all, &total)) { free(all); return EGL_FALSE; }
  for (EGLint i = 0; i < total; ++i) {
    if (has_extension(extensions(all[i], EGL_EXTENSIONS), "EGL_MESA_device_software")) {
      if (devices && *num_devices < max_devices) devices[*num_devices] = all[i];
      ++*num_devices;
    }
  }
  if (devices && *num_devices > max_devices) *num_devices = max_devices;
  free(all);
  return EGL_TRUE;
}

__eglMustCastToProperFunctionPointerType EGLAPIENTRY eglGetProcAddress(const char *name)
{
  if (name && strcmp(name, "eglQueryDevicesEXT") == 0)
    return (__eglMustCastToProperFunctionPointerType)eglQueryDevicesEXT;
  pthread_once(&egl_once, load_egl);
  return real_lookup ? real_lookup(name) : NULL;
}
