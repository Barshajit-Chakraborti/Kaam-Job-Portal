"""Shared form helpers: gives every widget the same Tailwind styling."""
from django import forms

INPUT = (
    "block w-full rounded-lg border border-line bg-white px-3.5 py-2.5 text-sm text-ink "
    "placeholder:text-muted/70 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30"
)
CHECK = "h-4 w-4 rounded border-line text-brand focus:ring-brand"
FILE = (
    "block w-full text-sm text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-tint "
    "file:px-3.5 file:py-2 file:text-sm file:font-medium file:text-brand hover:file:bg-brand/10"
)


class TailwindFormMixin:
    """Add Tailwind classes to every widget in the form (call before other init work)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.RadioSelect, forms.CheckboxSelectMultiple)):
                continue
            if isinstance(widget, forms.CheckboxInput):
                css = CHECK
            elif isinstance(widget, forms.FileInput):
                css = FILE
            else:
                css = INPUT
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()
