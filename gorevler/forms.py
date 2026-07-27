from django import forms
from .models import Talep


class TalepForm(forms.ModelForm): 
    class Meta:
        model = Talep
        fields = ['baslik', 'aciklama', 'birim', 'talep_turu', 'modul',
                  'hedef_surum', 'atanan', 'oncelik', 'hedef_tarih']

        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'birim': forms.Select(attrs={'class': 'form-select'}),
            'talep_turu': forms.Select(attrs={'class': 'form-select'}),
            'modul': forms.Select(attrs={'class': 'form-select'}),
            'hedef_surum': forms.TextInput(attrs={'class': 'form-control'}),
            'atanan': forms.Select(attrs={'class': 'form-select'}),
            'oncelik': forms.Select(attrs={'class': 'form-select'}),
            'hedef_tarih': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

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