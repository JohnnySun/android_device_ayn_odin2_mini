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

TARGET_BOARD_PLATFORM := kalama
TARGET_BOOTLOADER_BOARD_NAME := kalama
TARGET_BOARD_SUFFIX := _64
BOARD_VENDOR := ayn
BOARD_USES_QCOM_HARDWARE := true

TARGET_KERNEL_SOURCE := kernel/ayn/sm8550
TARGET_KERNEL_CONFIG := odin2_mini_defconfig
BOARD_KERNEL_CMDLINE := console=ttyMSM0,115200n8 androidboot.hardware=qcom

AB_OTA_UPDATER := true
AB_OTA_PARTITIONS += \
    boot \
    vendor_boot \
    dtbo \
    system \
    system_ext \
    product \
    vendor \
    odm

PRODUCT_SHIPPING_API_LEVEL := 33

-include vendor/ayn/odin2_mini/BoardConfigVendor.mk
