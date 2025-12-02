"""
Type definitions for PartsBox MCP Server.

This module provides TypedDict definitions for all PartsBox API entities.
These types enable strongly-typed responses and better IDE support.
"""

from typing import TypedDict


# =============================================================================
# Stock Types
# =============================================================================


class StockEntryData(TypedDict, total=False):
    """
    Stock entry representing inventory at a specific storage location.

    Required fields (always present):
        stock/quantity: Current stock quantity
        stock/storage-id: Storage location identifier
        stock/timestamp: Creation/update timestamp (UNIX UTC milliseconds)

    Optional fields:
        stock/id: Stock entry identifier (26-char compact UUID)
        stock/part-id: Part identifier
        stock/lot-id: Lot identifier
        stock/price: Unit price
        stock/currency: Currency code (e.g., 'usd', 'eur', 'gbp')
        stock/status: Stock status or null for on-hand
        stock/comments: Entry notes
        stock/order-id: Parent order identifier
        stock/vendor-sku: Vendor SKU that was ordered
        stock/custom-price?: Whether price was manually set
        stock/arriving: Expected delivery timestamp (UNIX UTC milliseconds)
        stock/user: User who created the entry
    """

    # Required fields
    stock_quantity: int  # stock/quantity
    stock_storage_id: str  # stock/storage-id
    stock_timestamp: int  # stock/timestamp

    # Optional fields
    stock_id: str  # stock/id
    stock_part_id: str  # stock/part-id
    stock_lot_id: str  # stock/lot-id
    stock_price: float  # stock/price
    stock_currency: str  # stock/currency
    stock_status: str | None  # stock/status
    stock_comments: str  # stock/comments
    stock_order_id: str  # stock/order-id
    stock_vendor_sku: str  # stock/vendor-sku
    stock_custom_price: bool  # stock/custom-price?
    stock_arriving: int  # stock/arriving
    stock_user: str  # stock/user


class SourceData(TypedDict, total=False):
    """
    Aggregated stock source data returned by storage/parts, storage/lots, etc.

    Required fields (always present):
        source/part-id: Part identifier (26-char compact UUID)
        source/storage-id: Storage location identifier
        source/lot-id: Lot identifier
        source/quantity: Aggregated stock quantity

    Optional fields:
        source/status: Stock status (ordered, reserved, etc.) or null for on-hand
        source/first-timestamp: UNIX timestamp of oldest stock entry
        source/last-timestamp: UNIX timestamp of most recent stock entry
    """

    source_part_id: str  # source/part-id
    source_storage_id: str  # source/storage-id
    source_lot_id: str  # source/lot-id
    source_quantity: int  # source/quantity
    source_status: str | None  # source/status
    source_first_timestamp: int  # source/first-timestamp
    source_last_timestamp: int  # source/last-timestamp


# =============================================================================
# Part Types
# =============================================================================


class PartAttritionData(TypedDict, total=False):
    """Part attrition settings for manufacturing."""

    percentage: float
    quantity: int


class PartLowStockData(TypedDict, total=False):
    """Part low stock threshold settings."""

    report: int


class PartData(TypedDict, total=False):
    """
    Part entity representing a component in the inventory.

    Required fields (always present):
        part/id: Part identifier (26-char compact UUID)
        part/name: Part name or internal identifier
        part/type: Part type (local, linked, sub-assembly, meta)
        part/created: Creation timestamp (UNIX UTC milliseconds)
        part/owner: Owner identifier

    Optional fields:
        part/description: Part description
        part/notes: User notes (Markdown supported)
        part/footprint: Physical package footprint
        part/manufacturer: Manufacturer name
        part/mpn: Manufacturer part number
        part/tags: List of tags
        part/linked-id: Linked part identifier (for linked parts)
        part/attrition: Attrition settings for manufacturing
        part/low-stock: Low stock threshold settings
        part/cad-keys: CAD keys for matching
        part/custom-fields: Custom field data
        part/stock: Stock history entries
    """

    # Required fields
    part_id: str  # part/id
    part_name: str  # part/name
    part_type: str  # part/type
    part_created: int  # part/created
    part_owner: str  # part/owner

    # Optional fields
    part_description: str | None  # part/description
    part_notes: str | None  # part/notes
    part_footprint: str | None  # part/footprint
    part_manufacturer: str | None  # part/manufacturer
    part_mpn: str | None  # part/mpn
    part_tags: list[str]  # part/tags
    part_linked_id: str  # part/linked-id
    part_attrition: PartAttritionData  # part/attrition
    part_low_stock: PartLowStockData  # part/low-stock
    part_cad_keys: list[str]  # part/cad-keys
    part_custom_fields: dict[str, object] | None  # part/custom-fields
    part_stock: list[StockEntryData]  # part/stock


# =============================================================================
# Lot Types
# =============================================================================


class LotData(TypedDict, total=False):
    """
    Lot entity representing a batch of parts with shared properties.

    Required fields (always present):
        lot/id: Lot identifier (26-char compact UUID)
        lot/created: Creation timestamp (UNIX UTC milliseconds)

    Optional fields:
        lot/name: Lot name or number
        lot/description: Short description
        lot/comments: Additional comments
        lot/expiration-date: Expiration timestamp (UNIX UTC milliseconds)
        lot/tags: List of tags
        lot/order-id: Linked order identifier
        lot/custom-fields: Custom field data
        lot/part-id: Part identifier (when returned in context)
        lot/storage-id: Storage location identifier (when returned in context)
        lot/quantity: Current quantity (when returned in context)
    """

    # Required fields
    lot_id: str  # lot/id
    lot_created: int  # lot/created

    # Optional fields
    lot_name: str | None  # lot/name
    lot_description: str | None  # lot/description
    lot_comments: str | None  # lot/comments
    lot_expiration_date: int | None  # lot/expiration-date
    lot_tags: list[str]  # lot/tags
    lot_order_id: str | None  # lot/order-id
    lot_custom_fields: dict[str, object] | None  # lot/custom-fields
    lot_part_id: str  # lot/part-id (contextual)
    lot_storage_id: str  # lot/storage-id (contextual)
    lot_quantity: int  # lot/quantity (contextual)


# =============================================================================
# Storage Types
# =============================================================================


class StorageData(TypedDict, total=False):
    """
    Storage location entity representing a place to store parts.

    Required fields (always present):
        storage/id: Storage location identifier (26-char compact UUID)
        storage/name: Storage location name

    Optional fields:
        storage/description: Storage location description
        storage/tags: List of tags
        storage/archived: Whether location is archived (default False)
        storage/full?: Whether location accepts new stock
        storage/single-part?: Single-part-only location
        storage/existing-parts-only?: Restrict to existing parts only
        storage/custom-fields: Custom field data
        storage/parent-id: Parent storage location identifier
        storage/path: Full path of location
        storage/comments: Additional comments
        storage/created: Creation timestamp (UNIX UTC milliseconds)
    """

    # Required fields
    storage_id: str  # storage/id
    storage_name: str  # storage/name

    # Optional fields
    storage_description: str | None  # storage/description
    storage_tags: list[str]  # storage/tags
    storage_archived: bool  # storage/archived
    storage_full: bool  # storage/full?
    storage_single_part: bool  # storage/single-part?
    storage_existing_parts_only: bool  # storage/existing-parts-only?
    storage_custom_fields: dict[str, object] | None  # storage/custom-fields
    storage_parent_id: str | None  # storage/parent-id
    storage_path: str  # storage/path
    storage_comments: str | None  # storage/comments
    storage_created: int  # storage/created


# =============================================================================
# Project Types
# =============================================================================


class ProjectData(TypedDict, total=False):
    """
    Project entity representing a BOM (Bill of Materials).

    Required fields (always present):
        project/id: Project identifier (26-char compact UUID)
        project/name: Project name

    Optional fields:
        project/description: Project description
        project/notes: Longer-form notes (Markdown supported)
        project/archived: Whether project is archived
        project/custom-fields: Custom field data
        project/created: Creation timestamp (UNIX UTC milliseconds)
        project/updated: Last update timestamp (UNIX UTC milliseconds)
        project/comments: Project comments
        project/entry-count: Number of BOM entries
    """

    # Required fields
    project_id: str  # project/id
    project_name: str  # project/name

    # Optional fields
    project_description: str | None  # project/description
    project_notes: str | None  # project/notes
    project_archived: bool  # project/archived
    project_custom_fields: dict[str, object] | None  # project/custom-fields
    project_created: int  # project/created
    project_updated: int  # project/updated
    project_comments: str | None  # project/comments
    project_entry_count: int  # project/entry-count


class ProjectEntryData(TypedDict, total=False):
    """
    BOM entry representing a part line item in a project.

    Required fields (always present):
        entry/id: Entry identifier (26-char compact UUID)
        entry/part-id: Part identifier
        entry/quantity: Quantity per board

    Optional fields:
        entry/name: BOM name for this entry
        entry/comments: Additional comments
        entry/designators: Set of designators (e.g., R1, R2, C1)
        entry/order: Ordering within the BOM
        entry/cad-footprint: Footprint from CAD program
        entry/cad-key: CAD key for matching to parts
        entry/custom-fields: Custom field data
    """

    # Required fields
    entry_id: str  # entry/id
    entry_part_id: str  # entry/part-id
    entry_quantity: int  # entry/quantity

    # Optional fields
    entry_name: str | None  # entry/name
    entry_comments: str | None  # entry/comments
    entry_designators: list[str] | str  # entry/designators (may be string or list)
    entry_order: int  # entry/order
    entry_cad_footprint: str | None  # entry/cad-footprint
    entry_cad_key: str | None  # entry/cad-key
    entry_custom_fields: dict[str, object] | None  # entry/custom-fields


class BuildData(TypedDict, total=False):
    """
    Build entity representing a manufacturing build of a project.

    Required fields (always present):
        build/id: Build identifier (26-char compact UUID)
        build/project-id: Parent project identifier

    Optional fields:
        build/created: Creation timestamp (UNIX UTC milliseconds)
        build/comments: Build notes/comments
        build/quantity: Number of units built
    """

    # Required fields
    build_id: str  # build/id
    build_project_id: str  # build/project-id

    # Optional fields
    build_created: int  # build/created
    build_comments: str | None  # build/comments
    build_quantity: int  # build/quantity


# =============================================================================
# Order Types
# =============================================================================


class OrderData(TypedDict, total=False):
    """
    Order entity representing a purchase order.

    Required fields (always present):
        order/id: Order identifier (26-char compact UUID)
        order/created: Creation timestamp (UNIX UTC milliseconds)

    Optional fields:
        order/vendor-name: Vendor or distributor name
        order/number: Vendor's order number
        order/invoice-number: Vendor's invoice number
        order/po-number: Purchase order number
        order/comments: Order comments
        order/notes: Additional notes (Markdown supported)
        order/arriving: Expected delivery timestamp (UNIX UTC milliseconds)
        order/tags: List of tags
        order/status: Order status (open, ordered, received)
        order/custom-fields: Custom field data
        order/vendor: Vendor name (legacy field)
    """

    # Required fields
    order_id: str  # order/id
    order_created: int  # order/created

    # Optional fields
    order_vendor_name: str | None  # order/vendor-name
    order_number: str | None  # order/number
    order_invoice_number: str | None  # order/invoice-number
    order_po_number: str | None  # order/po-number
    order_comments: str | None  # order/comments
    order_notes: str | None  # order/notes
    order_arriving: int | None  # order/arriving
    order_tags: list[str]  # order/tags
    order_status: str  # order/status
    order_custom_fields: dict[str, object] | None  # order/custom-fields
    order_vendor: str  # order/vendor (legacy)


class OrderEntryData(TypedDict, total=False):
    """
    Order entry representing a line item in an order.

    Required fields (always present):
        stock/id: Stock entry identifier
        stock/part-id: Part identifier
        stock/quantity: Quantity ordered
        stock/timestamp: Creation timestamp (UNIX UTC milliseconds)
        stock/order-id: Parent order identifier

    Optional fields:
        stock/storage-id: Storage location identifier (null until received)
        stock/lot-id: Lot identifier (null until received)
        stock/price: Unit price
        stock/currency: Currency code (e.g., USD, EUR)
        stock/status: Stock status (ordered, reserved, etc.)
        stock/comments: Entry notes
        stock/vendor-sku: Vendor SKU that was ordered
        stock/custom-price?: Whether price was manually set
        stock/arriving: Expected delivery date (UNIX UTC milliseconds)
    """

    # Required fields
    stock_id: str  # stock/id
    stock_part_id: str  # stock/part-id
    stock_quantity: int  # stock/quantity
    stock_timestamp: int  # stock/timestamp
    stock_order_id: str  # stock/order-id

    # Optional fields
    stock_storage_id: str | None  # stock/storage-id
    stock_lot_id: str | None  # stock/lot-id
    stock_price: float | None  # stock/price
    stock_currency: str | None  # stock/currency
    stock_status: str | None  # stock/status
    stock_comments: str | None  # stock/comments
    stock_vendor_sku: str | None  # stock/vendor-sku
    stock_custom_price: bool  # stock/custom-price?
    stock_arriving: int | None  # stock/arriving


# =============================================================================
# Note on field naming
# =============================================================================
#
# The PartsBox API uses field names with '/' characters (e.g., "part/name").
# TypedDict field names use underscores instead (e.g., "part_name").
#
# The actual API response data uses the original field names with slashes.
# These TypedDicts document the structure but cannot be used for direct
# type checking of API responses due to the slash characters in field names.
#
# When accessing fields from API responses, use the slash-style keys:
#   data["part/name"]  # correct
#   data["part_name"]  # incorrect - this key doesn't exist in the response
#
