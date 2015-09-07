# FtpBCM
Tool for binary control management over ftp

When you have a large project in dependencies, and you dont need to modify it constantly, then its march faster to build it just once on every revision, put the binaries on ftp server and then get in from ftp when you need it on other host.

```python 
# Somwhere in build script
from ftpBCM import ftpBCM

# init BCM
bcm = ftpBCM.FtpBCM('ftp server', 'user', 'password', 'project name')

# When we need to build project's new revision, first we check if it already exists on server
bcm.pull(path_to_project_binaries_for_platform_desktop_x86, project_source_revision, 'desktop_debug_x86')

# if not, then just build it.....

# When we've got binaries we push it server
bcm.push(path_to_project_binaries_for_platform_desktop_x86, project_source_revision, 'desktop_debug_x86')

# Now we have project's binaries on ftp, so next time we will not build it.

```
