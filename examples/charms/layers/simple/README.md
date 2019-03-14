Example from https://osm.etsi.org/gitweb/?p=osm/devops.git;a=tree;f=charms/layers/simple;h=bdf2957b5a5f6342bf24e3a675c21634d6064e3a;hb=HEAD

# Overview

This is an example charm as demonstrated in the OSM [Hackfest](https://osm.etsi.org/wikipub/index.php/OSM_workshops_and_events) series.

This is intended to provide a well-documented example of the proxy charm written by Hackfest participants.

# Prerequisites

There are two ways that you can exercise this charm: install the latest stable release of OSM or use Juju directly.

The workshop materials and tutorials cover using charms as part of OSM. You can follow that approach, but this README will focus on using Juju directly. We highly recommend that vendors and charm developers use this approach for the initial development of the charm.

## Ubuntu 16.04 or higher

We recommend using Ubuntu 16.04 or higher for the development and testing of charms. It is assumed that you have installed Ubuntu either on physical hardware or in a Virtual Machine.

## Install LXD and Juju

We will be installing the required software via snap. Snaps are containerised software packages, preferred because they are easy to create and install, will automatically update to the latest stable version, and contain bundled dependencies.

```
snap install lxd
snap install juju
snap install charm
```

# Usage


## Known Limitations and Issues

This not only helps users but gives people a place to start if they want to help
you add features to your charm.

# Configuration

The configuration options will be listed on the charm store, however If you're
making assumptions or opinionated decisions in the charm (like setting a default
administrator password), you should detail that here so the user knows how to
change it immediately, etc.

# Contact Information

## Upstream Project Name

  - Upstream website
  - Upstream bug tracker
  - Upstream mailing list or contact information
  - Feel free to add things if it's useful for users


[service]: http://example.com
[icon guidelines]: https://jujucharms.com/docs/stable/authors-charm-icon
