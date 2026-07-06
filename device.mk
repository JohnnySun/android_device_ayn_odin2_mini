DEVICE_PATH := device/ayn/odin2_mini

PRODUCT_SOONG_NAMESPACES += \
    $(DEVICE_PATH) \
    vendor/ayn/odin2_mini

PRODUCT_PROPERTY_OVERRIDES += \
    ro.product.vendor.device=kalama \
    ro.product.vendor.model=Odin2_Mini

PRODUCT_PACKAGES += \
    OdinSettings

$(call inherit-product, vendor/ayn/odin2_mini/odin2_mini-vendor.mk)
