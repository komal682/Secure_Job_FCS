from django import template

register = template.Library()

@register.filter
def get_other_participant(thread, user):
    """Returns the participant that is NOT the current user."""
    return thread.participants.exclude(id=user.id).first()
