from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.


class Stash(models.Model):
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    shared_with = models.ManyToManyField(get_user_model(), related_name='shared_stashes')

    def __str__(self):
        return self.name
    

class StashItem(models.Model):
    stash = models.ForeignKey(Stash, on_delete=models.CASCADE, related_name='items')
    identifier = models.CharField(max_length=100)
    object = models.CharField(max_length=100)
    added_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

