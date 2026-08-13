from django import forms
from .models import Talep


class TalepForm(forms.ModelForm):
    # Talep açan kişi atama yapmaz; talep departmana yönlendirilir.
    # Bu yüzden 'atanan' formda yer almaz; bunun yerine 'departman' seçilir.
    class Meta:
        model = Talep
        fields = ['baslik', 'aciklama', 'birim', 'talep_turu', 'modul',
                  'departman', 'hedef_surum', 'oncelik', 'hedef_tarih']

        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'birim': forms.Select(attrs={'class': 'form-select'}),
            'talep_turu': forms.Select(attrs={'class': 'form-select'}),
            'modul': forms.Select(attrs={'class': 'form-select'}),
            'departman': forms.Select(attrs={'class': 'form-select'}),
            'hedef_surum': forms.TextInput(attrs={'class': 'form-control'}),
            'oncelik': forms.Select(attrs={'class': 'form-select'}),
            'hedef_tarih': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Departman seçimi zorunlu (talebin yönlendirileceği yer).
        self.fields['departman'].required = True
        self.fields['departman'].queryset = (
            self.fields['departman'].queryset.filter(aktif=True)
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