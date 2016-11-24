from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(pre_save, sender=Log)
def generate_log_token(sender, instance, *args, **kwargs):
    if isinstance(instance, Log):
        if instance.message_token is None or instance.message_token == '':
            instance.generate_log_token(save=False)
