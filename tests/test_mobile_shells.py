"""
test_mobile_shells.py — Validation for mobile placeholder shells and cross-platform readiness.
"""
import os
import plistlib
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_ios_plist_structure():
    """Verify iOS Info.plist exists and contains required bundle keys."""
    plist_path = os.path.join(REPO_ROOT, "ios", "BDCN", "Info.plist")
    assert os.path.exists(plist_path), "Info.plist missing"

    with open(plist_path, "rb") as f:
        data = plistlib.load(f)
    assert data.get("CFBundleDisplayName") == "BDCN"
    assert data.get("CFBundleIdentifier") == "com.bdcn.app"
    assert "NSLocationWhenInUseUsageDescription" in data


def test_ios_app_delegate():
    """Verify iOS AppDelegate.swift entrypoint exists."""
    delegate_path = os.path.join(REPO_ROOT, "ios", "BDCN", "AppDelegate.swift")
    assert os.path.exists(delegate_path), "AppDelegate.swift missing"
    with open(delegate_path) as f:
        content = f.read()
    assert "UIApplicationDelegate" in content


def test_android_manifest_structure():
    """Verify AndroidManifest.xml exists and declares required package & permissions."""
    manifest_path = os.path.join(REPO_ROOT, "android", "app", "src", "main", "AndroidManifest.xml")
    assert os.path.exists(manifest_path), "AndroidManifest.xml missing"

    tree = ET.parse(manifest_path)
    root = tree.getroot()
    assert root.attrib.get("package") == "com.bdcn"

    permissions = [elem.attrib.get("{http://schemas.android.com/apk/res/android}name") for elem in root.findall("uses-permission")]
    assert "android.permission.INTERNET" in permissions
    assert "android.permission.ACCESS_COARSE_LOCATION" in permissions


def test_android_main_activity():
    """Verify Android MainActivity.kt entrypoint exists."""
    activity_path = os.path.join(REPO_ROOT, "android", "app", "src", "main", "java", "com", "bdcn", "MainActivity.kt")
    assert os.path.exists(activity_path), "MainActivity.kt missing"
    with open(activity_path) as f:
        content = f.read()
    assert "class MainActivity" in content
