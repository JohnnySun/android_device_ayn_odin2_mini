# Set the bring-up default before device.mk consumes the profile.
ODIN2_EARLY_TRACE ?= true

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)
$(call inherit-product, device/ayn/odin2_mini/device.mk)

ifeq ($(ODIN2_EARLY_TRACE),true)
WITH_ADB_INSECURE := true
endif

$(call inherit-product, vendor/lineage/config/common_full_phone.mk)

# M1 needs a recoverable first boot inside the stock-A-preserving super tail.
# These optional or stock Odin UI packages return during M2 hardware bring-up.
ifeq ($(ODIN2_COMMUNITY_M1_MINIMAL_PROFILE),true)
PRODUCT_PACKAGES += odin2_m1_minimal_profile
endif

ifeq ($(ODIN2_EARLY_TRACE),true)
PRODUCT_PACKAGES += \
    odin_boot_watchdog \
    odin_early_logger \
    odin_power_safety \
    odin_early_trace_rc
endif

PRODUCT_NAME := lineage_odin2_mini
PRODUCT_DEVICE := odin2_mini
PRODUCT_MANUFACTURER := AYN
PRODUCT_BRAND := AYN
PRODUCT_MODEL := Odin2 Mini

PRODUCT_SHIPPING_API_LEVEL := 33
PRODUCT_EXTRA_VNDK_VERSIONS := 33

ifeq ($(ODIN2_STOCK_CHAIN_PROFILE),true)
PRODUCT_BUILD_VENDOR_BOOT_IMAGE := false
endif

PRODUCT_GMS_CLIENTID_BASE := android-ayn
