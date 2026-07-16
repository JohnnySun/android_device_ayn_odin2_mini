DEVICE_PATH := device/ayn/odin2_mini

PRODUCT_SOONG_NAMESPACES += \
    $(DEVICE_PATH) \
    hardware/ayn \
    vendor/ayn/odin2_mini

DEVICE_PACKAGE_OVERLAYS += \
    $(DEVICE_PATH)/overlay

PRODUCT_PRODUCT_PROPERTIES += \
    ro.surface_flinger.primary_display_orientation=ORIENTATION_90

PRODUCT_USE_DYNAMIC_PARTITIONS := true
# Odin uses launch Virtual A/B without a standalone recovery image.
PRODUCT_BUILD_GENERIC_OTA_PACKAGE := true
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += $(DEVICE_PATH)/framework_compatibility_matrix.xml

$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/launch_with_vendor_ramdisk.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/generic_ramdisk.mk)

PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/displayconfig/display_layout_configuration.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/displayconfig/display_layout_configuration.xml \
    $(DEVICE_PATH)/idc/hyn_ts.idc:$(TARGET_COPY_OUT_SYSTEM)/usr/idc/hyn_ts.idc \
    $(DEVICE_PATH)/init/odinperformanced-device.rc:$(TARGET_COPY_OUT_SYSTEM)/etc/init/odinperformanced-device.rc \
    $(DEVICE_PATH)/keychars/Vendor_2020_Product_3001.kcm:$(TARGET_COPY_OUT_SYSTEM)/usr/keychars/Vendor_2020_Product_3001.kcm \
    $(DEVICE_PATH)/keylayout/Vendor_2020_Product_3001.kl:$(TARGET_COPY_OUT_SYSTEM)/usr/keylayout/Vendor_2020_Product_3001.kl \
    $(DEVICE_PATH)/permissions/odin2_mini_unavailable_features.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/permissions/odin2_mini_unavailable_features.xml \
    $(DEVICE_PATH)/vendor_ramdisk/.keep:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/.keep \
    $(DEVICE_PATH)/vendor_ramdisk/first_stage_ramdisk/fstab.qcom:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/first_stage_ramdisk/fstab.qcom

ifeq ($(ODIN2_EARLY_TRACE),true)
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/vendor_ramdisk/first_stage_ramdisk/fstab.stock_hybrid.qcom:$(TARGET_COPY_OUT_SYSTEM)/etc/fstab.odin2_hybrid.qcom
PRODUCT_SYSTEM_PROPERTIES += \
    ro.odin.debug_keepalive=1 \
    persist.sys.usb.config=adb \
    ro.adb.secure=0 \
    service.adb.root=1
endif

ifeq ($(ODIN2_HOST_TOOL_SOURCE_ROOT_PRUNE),true)
PRODUCT_SOURCE_ROOT_DIRS += \
    - \
    build \
    external/abseil-cpp \
    external/go-cmp \
    external/golang-protobuf \
    external/protobuf \
    external/pogreb \
    external/starlark-go \
    prebuilts \
    $(DEVICE_PATH) \
    vendor/ayn/odin2_mini \
    hardware/qcom-caf/sm8550 \
    hardware/qcom-caf/bootctrl \
    vendor/qcom/opensource/display \
    vendor/qcom/opensource/commonsys/display \
    vendor/qcom/opensource/commonsys-intf/display \
    hardware/qcom-caf/sm8550/data-ipa-cfg-mgr \
    vendor/qcom/opensource/dataservices \
    hardware/qcom-caf/thermal \
    hardware/qcom-caf/wlan \
    hardware/qcom-caf/wlan/qcwcn \
    system/extras/libjsonpb \
    system/extras/partition_tools \
    system/core/fs_mgr/liblp \
    system/core/libsparse \
    system/libbase \
    system/logging/liblog \
    system/tools/aidl/Android.bp \
    system/tools/aidl/build \
    system/tools/hidl/Android.bp \
    system/tools/hidl/build \
    toolchain/pgo-profiles/sampling
endif

ifeq ($(ODIN2_FULL_IMAGE_SOURCE_ROOT_PRUNE),true)
PRODUCT_SOURCE_ROOT_DIRS += \
    -external/cronet/tot \
    -external/swiftshader \
    -external/google-cloud-java \
    -external/aws-sdk-java-v2 \
    -external/pytorch \
    -external/executorch \
    -external/robolectric \
    -external/connectedappssdk \
	    -art/build/sdk \
	    -art/test \
	    platform_testing/libraries/motion/compose/values \
	    -platform_testing \
	    test/vts-testcase/hal/treble/vintf/libvts_vintf_test_common \
	    -test \
	    -test/cts-root \
    development/samples/AconfigDemo \
    -development/samples \
    -device/google \
    -hardware/google/gfxstream \
    -external/mesa3d \
    -frameworks/base/core/tests \
    -frameworks/base/libs/WindowManager/Shell/tests \
    -frameworks/base/libs/WindowManager/Jetpack/tests \
    -frameworks/base/media/tests \
    -frameworks/base/services/tests \
    -frameworks/base/tests \
    -frameworks/base/cmds/uinput/tests \
    -packages/modules/AdServices/shared/tests \
    -packages/modules/ConfigInfrastructure/framework/tests \
    -packages/apps/Car \
    -packages/services/Car/tests \
    -trusty/vendor/google/aosp/scripts
endif

PRODUCT_PACKAGES_DEBUG += \
    thermal_selftest

PRODUCT_PACKAGES += \
    OdinSettings \
    android.hardware.thermal-service.qti \
    odinfand \
    odinperformanced \
    rsinputd

$(call inherit-product, vendor/ayn/odin2_mini/odin2_mini-vendor.mk)
