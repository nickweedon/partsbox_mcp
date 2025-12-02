"""
Type definitions for PartsBox MCP Server.

This module provides TypedDict definitions for all PartsBox API entities.
These types enable strongly-typed responses and better IDE support.
"""

from typing import TypedDict


# =============================================================================
# Stock Types
# =============================================================================

# Note: We use functional TypedDict syntax to allow field names with '/' characters
# that match the actual PartsBox API field names.

StockEntryData = TypedDict('StockEntryData', {
    # Required fields
    'stock/quantity': int,
    'stock/storage-id': str,
    'stock/timestamp': int,
    # Optional fields
    'stock/id': str,
    'stock/part-id': str,
    'stock/lot-id': str,
    'stock/price': float,
    'stock/currency': str,
    'stock/status': str | None,
    'stock/comments': str,
    'stock/order-id': str,
    'stock/vendor-sku': str,
    'stock/custom-price?': bool,
    'stock/arriving': int,
    'stock/user': str,
    'stock/linked?': bool,
}, total=False)
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
    stock/linked?: Whether this entry is linked to another (e.g., paired move entries)
"""

SourceData = TypedDict('SourceData', {
    'source/part-id': str,
    'source/storage-id': str,
    'source/lot-id': str,
    'source/quantity': int,
    'source/status': str | None,
    'source/first-timestamp': int,
    'source/last-timestamp': int,
}, total=False)
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


# =============================================================================
# Part Types
# =============================================================================

# Note: We use functional TypedDict syntax to allow field names with '/' characters
# that match the actual PartsBox API field names.

PartAttritionData = TypedDict('PartAttritionData', {
    'percentage': float,
    'quantity': int,
}, total=False)
"""Part attrition settings for manufacturing."""

PartLowStockData = TypedDict('PartLowStockData', {
    'report': int,
}, total=False)
"""Part low stock threshold settings."""

PartData = TypedDict('PartData', {
    # Required fields
    'part/id': str,
    'part/name': str,
    'part/type': str,
    'part/created': int,
    'part/owner': str,
    # Optional fields
    'part/description': str | None,
    'part/notes': str | None,
    'part/footprint': str | None,
    'part/manufacturer': str | None,
    'part/mpn': str | None,
    'part/tags': list[str],
    'part/linked-id': str,
    'part/img-id': str | None,
    'part/attrition': PartAttritionData,
    'part/low-stock': PartLowStockData,
    'part/cad-keys': list[str],
    'part/custom-fields': dict[str, object] | None,
    'part/stock': list['StockEntryData'],
}, total=False)
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
    part/img-id: Image identifier for the part's associated image
    part/attrition: Attrition settings for manufacturing
    part/low-stock: Low stock threshold settings
    part/cad-keys: CAD keys for matching
    part/custom-fields: Custom field data
    part/stock: Stock history entries
"""


# =============================================================================
# Lot Types
# =============================================================================

LotData = TypedDict('LotData', {
    # Required fields
    'lot/id': str,
    'lot/created': int,
    # Optional fields
    'lot/name': str | None,
    'lot/description': str | None,
    'lot/comments': str | None,
    'lot/expiration-date': int | None,
    'lot/tags': list[str],
    'lot/order-id': str | None,
    'lot/custom-fields': dict[str, object] | None,
    'lot/part-id': str,
    'lot/storage-id': str,
    'lot/quantity': int,
}, total=False)
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


# =============================================================================
# Storage Types
# =============================================================================

StorageData = TypedDict('StorageData', {
    # Required fields
    'storage/id': str,
    'storage/name': str,
    # Optional fields
    'storage/description': str | None,
    'storage/tags': list[str],
    'storage/archived': bool,
    'storage/full?': bool,
    'storage/single-part?': bool,
    'storage/existing-parts-only?': bool,
    'storage/custom-fields': dict[str, object] | None,
    'storage/parent-id': str | None,
    'storage/path': str,
    'storage/comments': str | None,
    'storage/created': int,
}, total=False)
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


# =============================================================================
# Project Types
# =============================================================================

ProjectData = TypedDict('ProjectData', {
    # Required fields
    'project/id': str,
    'project/name': str,
    # Optional fields
    'project/description': str | None,
    'project/notes': str | None,
    'project/archived': bool,
    'project/custom-fields': dict[str, object] | None,
    'project/created': int,
    'project/updated': int,
    'project/comments': str | None,
    'project/entry-count': int,
}, total=False)
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

ProjectEntryData = TypedDict('ProjectEntryData', {
    # Required fields
    'entry/id': str,
    'entry/part-id': str,
    'entry/quantity': int,
    # Optional fields
    'entry/name': str | None,
    'entry/comments': str | None,
    'entry/designators': list[str] | str,
    'entry/order': int,
    'entry/cad-footprint': str | None,
    'entry/cad-key': str | None,
    'entry/custom-fields': dict[str, object] | None,
}, total=False)
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

BuildData = TypedDict('BuildData', {
    # Required fields
    'build/id': str,
    'build/project-id': str,
    # Optional fields
    'build/created': int,
    'build/comments': str | None,
    'build/quantity': int,
}, total=False)
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


# =============================================================================
# Order Types
# =============================================================================

OrderData = TypedDict('OrderData', {
    # Required fields
    'order/id': str,
    'order/created': int,
    # Optional fields
    'order/vendor-name': str | None,
    'order/number': str | None,
    'order/invoice-number': str | None,
    'order/po-number': str | None,
    'order/comments': str | None,
    'order/notes': str | None,
    'order/arriving': int | None,
    'order/tags': list[str],
    'order/status': str,
    'order/custom-fields': dict[str, object] | None,
    'order/vendor': str,
}, total=False)
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

OrderEntryData = TypedDict('OrderEntryData', {
    # Required fields
    'stock/id': str,
    'stock/part-id': str,
    'stock/quantity': int,
    'stock/timestamp': int,
    'stock/order-id': str,
    # Optional fields
    'stock/storage-id': str | None,
    'stock/lot-id': str | None,
    'stock/price': float | None,
    'stock/currency': str | None,
    'stock/status': str | None,
    'stock/comments': str | None,
    'stock/vendor-sku': str | None,
    'stock/custom-price?': bool,
    'stock/arriving': int | None,
}, total=False)
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
