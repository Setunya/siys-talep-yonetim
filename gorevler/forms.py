from django import forms
from .models import Talep


class TalepForm(forms.ModelForm):
    # Talep açan kişi atama YAPMAZ ve departman SEÇMEZ.
    # Departman, seçilen Modül'e (konuya) göre sistem tarafından otomatik atanır.
    class Meta:
        model = Talep
        fields = ['baslik', 'aciklama', 'birim', 'talep_turu', 'modul',
                  'hedef_surum', 'oncelik', 'hedef_tarih']

        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'birim': forms.Select(attrs={'class': 'form-select'}),
            'talep_turu': forms.Select(attrs={'class': 'form-select'}),
            'modul': forms.Select(attrs={'class': 'form-select'}),
            'hedef_surum': forms.TextInput(attrs={'class': 'form-control'}),
            'oncelik': forms.Select(attrs={'class': 'form-select'}),
            'hedef_tarih': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Yalnızca bir departmana bağlı (yönlendirilebilir) modüller seçilebilir;
        # böylece açılan her talep mutlaka bir departman müdürüne ulaşır.
        self.fields['modul'].queryset = self.fields['modul'].queryset.filter(
            aktif=True, departman__isnull=False
        )

from .models import Yorum


class YorumForm(forms.ModelForm):
    class Meta:
        model = Yorum
        fields = ['metin']
        widgets = {
            'metin': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Yorumunuzu yazın...'
            }),
        }