# Lok (Next)

[![codecov](https://codecov.io/gh/arkitektio/lok-server-next/branch/main/graph/badge.svg?token=UGXEA2THBV)](https://codecov.io/gh/arkitektio/lok-server-next)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/arkitektio/lok-server-next/)
![Maintainer](https://img.shields.io/badge/maintainer-jhnnsrs-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/jhnnsrs/arkitektio/lok-server-next)

Lok is a central backend to manage and authorize User and Applications in a distributed
settings. Loks provides endpoints for apps to configure themselvers (through the Fakts protocol)
and in a second step to authenticate and authorize users. For the latter it is build on top of [Oauth2](https://oauth.net/2/)
and [OpenID Connect](https://openid.net/connect/). It then provides a central authentication and authorization
service for applications to register and authenticate users, and issues JWT token for accessing services.

As JWT are cryptographically signed, they can be verified by any service, and do not require
a central session store. 

This distributed and scalable authentication and authorization system, was developed as the backbone for the
Arkitekt platform, but can be used as a standalone service for any application.

> [!NOTE]  
> What you are currently lo(o)king at is the next version of Lok. It is currently under development and not ready for production. If you are looking for the current version of Lok, you can find it [here](https://github.com/arkitektio/lok-server-next).


Check out the [documentation](https://arkitekt.live/docs/services/lok) for more information.


## Roadmap

This is the current roadmap for the merging of the new version of Lok into the main repository:

- [x] Application Registration (Authentication of apps based on various Flows)
- [x] App Configuration (apps can retrieve their configuration from the server)
- [x] User Authentication and Authorization
- [x] User and Application Management
- [x] Distibuted Authentication
- [x] Social Features (Comments) 
- [x] User Profiles
- [x] More diverse App Registration Flows (e.g. for Websites)
- [x] Social Login (Login with Orcid, Github, Google,... )
- [ ] User Profiles with social account information
- [x] Notificaition Backend (with Mobile Push Notifications) (channels)
- [ ] More Security Features (e.g. 2FA)
- [ ] CI/CD Pipeline (testing against both old and new apps)
- [ ] Documentation

