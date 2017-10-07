from django.contrib import admin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from .models import NucleicAcidType, Sample


@admin.register(NucleicAcidType)
class NucleicAcidTypeAdmin(admin.ModelAdmin):
    list_filter = ('type',)


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'request_name', 'library_protocol',
                    'library_type',)
    list_select_related = True
    readonly_fields = ('create_time', 'update_time',)

    search_fields = ('name', 'barcode', 'library_protocol__name',
                     'library_type__name', 'request__name',)

    list_filter = (('library_protocol', RelatedDropdownFilter),
                   ('library_type', RelatedDropdownFilter),
                   ('nucleic_acid_type', RelatedDropdownFilter),
                   ('concentration_method', RelatedDropdownFilter),
                   ('organism', RelatedDropdownFilter),
                   ('read_length', RelatedDropdownFilter),
                   ('index_type', RelatedDropdownFilter),)

    fieldsets = (
        (None, {
            'fields': ('name', 'status', 'barcode', 'is_pooled',
                       'is_converted',),
        }),
        ('Determined by User', {
            'fields': ('library_protocol', 'library_type', 'nucleic_acid_type',
                       'concentration', 'concentration_method', 'organism',
                       'read_length', 'sequencing_depth',
                       'equal_representation_nucleotides', 'index_type',
                       'index_i7', 'index_i5', 'rna_quality',
                       'amplification_cycles', 'comments',),
        }),
        ('Determined by Facility', {
            'fields': ('dilution_factor', 'concentration_facility',
                       'concentration_method_facility',
                       'sample_volume_facility', 'amount_facility',
                       'size_distribution_facility', 'rna_quality_facility',
                       'comments_facility',),
        }),
        ('Other', {
            'fields': ('create_time', 'update_time',),
        }),
    )

    def request_name(self, obj):
        request = obj.request.filter()
        return request[0].name if request else None
