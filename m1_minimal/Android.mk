# SPDX-License-Identifier: Apache-2.0

# NOT IN ANY BUILD. Nothing adds odin2_m1_minimal_profile to PRODUCT_PACKAGES,
# so /system/etc/odin2_m1_minimal_profile has never existed on the device and
# the LOCAL_OVERRIDES_MODULES list below has never suppressed anything: Jelly,
# Gallery2, Twelve and Aperture are all installed despite being named here, and
# TouchMapping shipped for months while listed here too. Read this file as a
# statement of intent, never as a description of what the image contains.
# Wiring it up removes a dozen applications and is a product decision.

LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := odin2_m1_minimal_profile
LOCAL_MODULE_CLASS := ETC
LOCAL_MODULE_TAGS := optional
LOCAL_MODULE_PATH := $(TARGET_OUT_ETC)
LOCAL_MODULE_STEM := odin2_m1_minimal_profile
LOCAL_SRC_FILES := odin2_m1_minimal_profile
LOCAL_OVERRIDES_MODULES := \
    Aperture \
    AudioFX \
    AvatarPicker \
    Backgrounds \
    BuiltInPrintService \
    Camelot \
    DeviceAsWebcam \
    DeviceDiagnostics \
    EasterEgg \
    Etar \
    Gallery2 \
    GameAssistant \
    Glimpse \
    Jelly \
    LiveWallpapersPicker \
    PhotoTable \
    PrintRecommendationService \
    PrintSpooler \
    QuickAccessWallet \
    Recorder \
    Seedvault \
    ThemePicker \
    TouchMapping \
    Twelve \
    Updater \
    bash \
    htop \
    nano \
    rsync \
    unrar \
    vim
include $(BUILD_PREBUILT)
