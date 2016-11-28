from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from gaming.models import Log


@receiver(pre_save, sender=Log)
def generate_log_token(sender, instance, *args, **kwargs):
    if isinstance(instance, Log):
        if instance.message_token is None or instance.message_token == '':
            instance.generate_log_token(save=False)


@receiver(post_save, sender=Log)
def email_log(sender, instance, *args, **kwargs):
    if isinstance(instance, Log):
        if instance.email:
            if instance.subject is None or instance.subject == '':
                subject = "Log item needs your attention"
            else:
                subject = instance.subject
            if instance.body is None or instance.body == '':
                body = instance.message
            else:
                body = instance.body

            send_mail(
                subject='{} {}'.format(settings.EMAIL_SUBJECT_PREFIX, subject),
                message="Message Token: {}\n\n{}".format(instance.message_token, body),
                from_email=settings.SERVER_EMAIL,
                recipient_list=settings.ADMINS,
                fail_silently=True
            )
