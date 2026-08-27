# SPDX-License-Identifier: Apache-2.0

# In the community build lane only. lineage_odin2_mini.mk adds this module
# behind ODIN2_COMMUNITY_M1_MINIMAL_PROFILE, which tools/lineage-community-erofs-build.sh
# exports and nothing else does - so a build driven straight from
# `m systemimage systemextimage`, which is how every candidate from v62 onward
# was made, does not contain it and none of the overrides below apply.
#
# That is why the device shows Jelly, Gallery2, Twelve and Aperture despite
# their being named here, and why TouchMapping shipped for months the same way.
# An earlier version of this comment said "NOT IN ANY BUILD. Nothing adds
# odin2_m1_minimal_profile to PRODUCT_PACKAGES", which is false and was read as
# meaning the list was inert everywhere.
#
# So: this list is a description of the community lane and a statement of
# intent everywhere else. Making it apply to every build removes a dozen
# applications and is a product decision, not a cleanup.

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
