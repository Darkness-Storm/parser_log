from django import forms


class SearchForm(forms.Form):
    search = forms.CharField(label='Поиск', max_length=100)