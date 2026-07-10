# Changelog

## [Unreleased]

### Added

- **feat(ARCH-3836): Refinements - BCDN**

  This introduces a comprehensive set of features to the Blood Donor Connection Network, focusing on donor engagement and administrative efficiency. The key additions are:

  - **Donor Portal and Social Login**: A complete donor-facing portal has been introduced, allowing users to register, log in with a username/password, or use social media accounts (Google, Apple, Facebook). This is supported by new routes and templates, including `login_donor.html` and `register_donor.html`.

  - **Gamification and Donor Profiles**: To encourage donations, a gamification engine has been implemented. Donors can now earn badges (`Bronze Savior`, `Silver Savior`, `Gold Guardian`) based on their donation history. A new `donor_profile.html` template displays these achievements and personal donation history.

  - **Privacy-First Geolocation**: A donor density map (`map_hotspots.html`) has been added, which simulates Google Maps clustering to show donor hotspots without revealing personal addresses. This feature includes filtering by radius and blood type, enhancing privacy while providing valuable information to recipients.

  - **Enhanced Recipient and Admin Functionality**: Blood demand requests can now be submitted with an `urgency` level and `district` selection, allowing for better prioritization. Administrators can filter the verification queue by district to streamline the approval process.
