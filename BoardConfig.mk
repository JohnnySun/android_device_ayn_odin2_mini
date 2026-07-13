DEVICE_PATH := device/ayn/odin2_mini

TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_ABI2 :=
TARGET_CPU_VARIANT := generic

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic
TARGET_SUPPORTS_64_BIT_APPS := true

TARGET_BOARD_PLATFORM := kalama
TARGET_BOOTLOADER_BOARD_NAME := kalama
TARGET_BOARD_SUFFIX := _64
BOARD_VENDOR := ayn
BOARD_USES_QCOM_HARDWARE := true

TARGET_KERNEL_SOURCE := kernel/ayn/sm8550
TARGET_KERNEL_CONFIG := odin2_mini_defconfig
BOARD_KERNEL_IMAGE_NAME := Image
ODIN2_MINI_BOOT_KERNEL_MODULES_LIST := $(DEVICE_PATH)/kernel/boot.modules.load
BOOT_KERNEL_MODULES := $(strip $(shell cat $(ODIN2_MINI_BOOT_KERNEL_MODULES_LIST)))
BOARD_VENDOR_RAMDISK_KERNEL_MODULES_LOAD := $(BOOT_KERNEL_MODULES)
BOARD_KERNEL_CMDLINE := console=ttyMSM0,115200n8 androidboot.hardware=qcom
BOARD_KERNEL_BASE := 0x00000000
BOARD_KERNEL_PAGESIZE := 4096
TARGET_KERNEL_MIXED_MODE := false

# First userspace bring-up favors complete runtime JARs over host-side odex
# generation. Re-enable dexpreopt after the full product graph is stable.
WITH_DEXPREOPT := false

# Stock by-name sizes from read-only inventory:
# boot/vendor_boot: 98,304 KiB; init_boot: 8,192 KiB; dtbo: 24,576 KiB;
# recovery: 102,400 KiB.
BOARD_BOOTIMAGE_PARTITION_SIZE := 100663296
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 100663296
BOARD_INIT_BOOT_IMAGE_PARTITION_SIZE := 8388608
BOARD_DTBOIMG_PARTITION_SIZE := 25165824
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 104857600
ODIN2_STOCK_BOOTIMAGE ?= $(DEVICE_PATH)/prebuilt-private/boot.img
ODIN2_STOCK_VENDOR_BOOTIMAGE ?= $(DEVICE_PATH)/prebuilt-private/vendor_boot.img
ODIN2_STOCK_RECOVERYIMAGE ?= $(DEVICE_PATH)/prebuilt-private/recovery.img
ODIN2_STOCK_DTBOIMAGE ?= $(DEVICE_PATH)/prebuilt-private/dtbo.img
ODIN2_STOCK_VENDORIMAGE ?= $(DEVICE_PATH)/prebuilt-private/vendor.img
ODIN2_STOCK_ODMIMAGE ?= $(DEVICE_PATH)/prebuilt-private/odm.img
ODIN2_STOCK_VENDOR_DLKMIMAGE ?= $(DEVICE_PATH)/prebuilt-private/vendor_dlkm.img
ODIN2_STOCK_SYSTEM_DLKMIMAGE ?= $(DEVICE_PATH)/prebuilt-private/system_dlkm.img
ODIN2_STOCK_CHAIN_PROFILE ?= false
ODIN2_STOCK_CHAIN_REQUIRED_IMAGES := \
    $(ODIN2_STOCK_BOOTIMAGE) \
    $(ODIN2_STOCK_VENDOR_BOOTIMAGE) \
    $(ODIN2_STOCK_RECOVERYIMAGE) \
    $(ODIN2_STOCK_DTBOIMAGE) \
    $(ODIN2_STOCK_VENDORIMAGE) \
    $(ODIN2_STOCK_ODMIMAGE) \
    $(ODIN2_STOCK_VENDOR_DLKMIMAGE) \
    $(ODIN2_STOCK_SYSTEM_DLKMIMAGE)
ifeq ($(ODIN2_STOCK_CHAIN_PROFILE),true)
ifneq ($(words $(wildcard $(ODIN2_STOCK_CHAIN_REQUIRED_IMAGES))),8)
$(error ODIN2_STOCK_CHAIN_PROFILE requires every frozen stock image input)
endif
BOARD_PREBUILT_BOOTIMAGE := $(ODIN2_STOCK_BOOTIMAGE)
BOARD_PREBUILT_VENDOR_BOOTIMAGE := $(ODIN2_STOCK_VENDOR_BOOTIMAGE)
BOARD_PREBUILT_RECOVERYIMAGE := $(ODIN2_STOCK_RECOVERYIMAGE)
BOARD_PREBUILT_VENDORIMAGE := $(ODIN2_STOCK_VENDORIMAGE)
BOARD_PREBUILT_ODMIMAGE := $(ODIN2_STOCK_ODMIMAGE)
BOARD_PREBUILT_VENDOR_DLKMIMAGE := $(ODIN2_STOCK_VENDOR_DLKMIMAGE)
BOARD_PREBUILT_SYSTEM_DLKMIMAGE := $(ODIN2_STOCK_SYSTEM_DLKMIMAGE)
ODIN2_EXACT_STOCK_PREBUILT_BOOT_CHAIN := true
ODIN2_BUILD_MANIFEST_CHECKED_OUT_ONLY := true
BOARD_AVB_FROZEN_PARTITIONS := \
    boot \
    vendor_boot \
    recovery \
    dtbo \
    vendor \
    odm \
    vendor_dlkm \
    system_dlkm
BOARD_AVB_FROZEN_PROFILE := odin2_stock_chain_v1
# The stock top-level vbmeta authenticates only the meaningful dtbo payload;
# the partition dump itself is padded to the full by-name partition size.
BOARD_AVB_FROZEN_DTBO_DESCRIPTOR_IMAGE_SIZE := 12663075
ODIN2_STOCK_FROZEN_PARTITION_FINGERPRINT := qti/kalama/kalama:13/TKQ1.231222.001/Odin2Mini06261540:user/release-keys
BOARD_AVB_FROZEN_VENDOR_CARE_MAP_PROPERTY_ID := ro.vendor.build.fingerprint
BOARD_AVB_FROZEN_VENDOR_CARE_MAP_FINGERPRINT := $(ODIN2_STOCK_FROZEN_PARTITION_FINGERPRINT)
BOARD_AVB_FROZEN_ODM_CARE_MAP_PROPERTY_ID := ro.odm.build.fingerprint
BOARD_AVB_FROZEN_ODM_CARE_MAP_FINGERPRINT := $(ODIN2_STOCK_FROZEN_PARTITION_FINGERPRINT)
BOARD_AVB_FROZEN_VENDOR_DLKM_CARE_MAP_PROPERTY_ID := ro.vendor_dlkm.build.fingerprint
BOARD_AVB_FROZEN_VENDOR_DLKM_CARE_MAP_FINGERPRINT := $(ODIN2_STOCK_FROZEN_PARTITION_FINGERPRINT)
BOARD_AVB_FROZEN_SYSTEM_DLKM_CARE_MAP_PROPERTY_ID := ro.system_dlkm.build.fingerprint
BOARD_AVB_FROZEN_SYSTEM_DLKM_CARE_MAP_FINGERPRINT := $(ODIN2_STOCK_FROZEN_PARTITION_FINGERPRINT)
TARGET_NO_KERNEL := true
endif
BOARD_BOOT_HEADER_VERSION := 4
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)
BOARD_INIT_BOOT_HEADER_VERSION := 4
BOARD_MKBOOTIMG_INIT_ARGS += --header_version $(BOARD_INIT_BOOT_HEADER_VERSION)
# Match the stock init_boot ramdisk contract. The stock kernel supports both
# formats, but the shipping image uses the Linux-compatible LZ4 legacy frame.
BOARD_RAMDISK_USE_LZ4 := true
BOARD_USES_METADATA_PARTITION := true
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/vendor_ramdisk/first_stage_ramdisk/fstab.qcom

BOARD_AVB_ENABLE := true
BOARD_AVB_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VBMETA_SYSTEM := system system_ext product
BOARD_AVB_VBMETA_SYSTEM_KEY_PATH := external/avb/test/data/testkey_rsa2048.pem
BOARD_AVB_VBMETA_SYSTEM_ALGORITHM := SHA256_RSA2048
# Match stock A's system-chain rollback floor until persistent device state is
# captured and a higher index is proven not to invalidate rollback.
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX := 1704067200
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX_LOCATION := 2

# Early-trace images are temporary diagnostics. Keep dm-verity and the signed
# hash tree, but omit optional FEC so trace growth cannot resize system_b.
ifeq ($(ODIN2_EARLY_TRACE),true)
BOARD_AVB_SYSTEM_ADD_HASHTREE_FOOTER_ARGS += --do_not_generate_fec
endif

ifeq ($(ODIN2_STOCK_CHAIN_PROFILE),true)
TARGET_RO_FILE_SYSTEM_TYPE := ext4
else
TARGET_RO_FILE_SYSTEM_TYPE := erofs
endif
BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := $(TARGET_RO_FILE_SYSTEM_TYPE)
BOARD_PRODUCTIMAGE_FILE_SYSTEM_TYPE := $(TARGET_RO_FILE_SYSTEM_TYPE)
BOARD_SYSTEM_EXTIMAGE_FILE_SYSTEM_TYPE := $(TARGET_RO_FILE_SYSTEM_TYPE)

BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := $(TARGET_RO_FILE_SYSTEM_TYPE)
BOARD_ODMIMAGE_FILE_SYSTEM_TYPE := $(TARGET_RO_FILE_SYSTEM_TYPE)
BOARD_VENDOR_DLKMIMAGE_FILE_SYSTEM_TYPE := $(TARGET_RO_FILE_SYSTEM_TYPE)
BOARD_SYSTEM_DLKMIMAGE_FILE_SYSTEM_TYPE := $(TARGET_RO_FILE_SYSTEM_TYPE)

TARGET_COPY_OUT_PRODUCT := product
TARGET_COPY_OUT_SYSTEM_EXT := system_ext
TARGET_COPY_OUT_VENDOR := vendor
TARGET_COPY_OUT_ODM := odm
TARGET_COPY_OUT_VENDOR_DLKM := vendor_dlkm
TARGET_COPY_OUT_SYSTEM_DLKM := system_dlkm

BOARD_SUPER_PARTITION_SIZE := 5679575040
BOARD_SUPER_PARTITION_GROUPS := qti_dynamic_partitions
BOARD_QTI_DYNAMIC_PARTITIONS_PARTITION_LIST := \
    system \
    system_ext \
    product \
    vendor \
    odm \
    vendor_dlkm \
    system_dlkm

# Stock lpdump reports both Virtual A/B groups with this maximum. The groups
# share physical super capacity; they are not statically split in half.
BOARD_QTI_DYNAMIC_PARTITIONS_SIZE := 5675380736
BOARD_BUILD_SUPER_IMAGE_BY_DEFAULT := true
BOARD_SUPER_IMAGE_IN_UPDATE_PACKAGE := true

AB_OTA_UPDATER := true
# Keep dtbo out of AB_OTA_PARTITIONS until a real stock or kernel-generated
# dtbo.img is wired through BOARD_PREBUILT_DTBOIMAGE.
AB_OTA_PARTITIONS += \
    boot \
    init_boot \
    vendor_boot \
    system \
    system_ext \
    product \
    vendor \
    odm \
    vendor_dlkm \
    system_dlkm \
    vbmeta \
    vbmeta_system

ifeq ($(ODIN2_STOCK_CHAIN_PROFILE),true)
AB_OTA_PARTITIONS += recovery
endif

-include vendor/ayn/odin2_mini/BoardConfigVendor.mk

ifeq ($(ODIN2_STOCK_CHAIN_PROFILE),true)
BOARD_PREBUILT_DTBOIMAGE := $(ODIN2_STOCK_DTBOIMAGE)
endif

ifneq ($(BOARD_PREBUILT_DTBIMAGE_DIR),)
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
endif

ifneq ($(BOARD_PREBUILT_DTBOIMAGE),)
AB_OTA_PARTITIONS += dtbo
endif
