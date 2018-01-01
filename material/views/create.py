from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms.models import modelform_factory
from django.utils.html import format_html
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from material.viewset import viewprop

from .base import FormLayoutMixin, has_object_perm


class CreateModelView(FormLayoutMixin, generic.CreateView):
    viewset = None
    layout = None
    form_widgets = None

    template_name_suffix = '_create'

    def has_add_permission(self, request):
        if self.viewset is not None:
            return self.viewset.has_add_permission(request)
        else:
            return has_object_perm(request.user, 'add', self.model)

    def get_object_url(self, obj):
        if self.viewset is not None and hasattr(self.viewset, 'get_object_url'):
            return self.viewset.get_object_url(self.request, obj)
        elif hasattr(obj, 'get_absolute_url'):
            if has_object_perm(self.request.user, 'change', obj):
                return obj.get_absolute_url()

    def message_user(self):
        url = self.get_object_url(self.object)
        link = ''
        if url:
            link = format_html('<a href="{}">{}</a>', urlquote(url), _('View'))

        message = format_html(
            _("The {obj} was added successfully. {link}"),
            obj=str(self.object),
            link=link
        )
        messages.add_message(self.request, messages.SUCCESS, message, fail_silently=True)

    @viewprop
    def queryset(self):
        if self.viewset is not None and hasattr(self.viewset, 'get_queryset'):
            return self.viewset.get_queryset(self.request)
        return None

    def get_form_class(self):
        if self.form_class is None:
            return modelform_factory(self.model, fields=self.fields, widgets=self.form_widgets)
        return self.form_class

    def get_template_names(self):
        """
        List of templates for the view.
        If no `self.template_name` defined, uses::
             [<app_label>/<model_label>_<suffix>.html,
              <app_label>/<model_label>_form.html,
              'material/views/form.html']
        """
        if self.template_name is None:
            opts = self.model._meta
            return [
                '{}/{}{}.html'.format(opts.app_label, opts.model_name, self.template_name_suffix),
                '{}/{}_form.html'.format(opts.app_label, opts.model_name),
                'material/views/form.html',
            ]

    def form_valid(self, *args, **kwargs):
        response = super(CreateModelView, self).form_valid(*args, **kwargs)
        self.message_user()
        return response

    def get_success_url(self):
        return '/'  # TODO

    def dispatch(self, request, *args, **kwargs):
        if not self.has_add_permission(self.request):
            raise PermissionDenied

        return super(CreateModelView, self).dispatch(request, *args, **kwargs)
