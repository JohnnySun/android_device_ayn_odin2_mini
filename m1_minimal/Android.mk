# SPDX-License-Identifier: Apache-2.0

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
