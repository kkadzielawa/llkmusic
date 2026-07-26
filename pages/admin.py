from django.contrib import admin

from .models import Course, Order, OrderItem


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'display_order', 'updated_at')
    list_editable = ('price', 'is_available', 'display_order')
    list_filter = ('is_available', 'category')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description', 'slug')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_id', 'product_name', 'unit_price', 'quantity', 'line_total')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'customer_email', 'subtotal', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_email', 'items__product_name')
    readonly_fields = ('order_number', 'subtotal', 'created_at')
    inlines = (OrderItemInline,)
