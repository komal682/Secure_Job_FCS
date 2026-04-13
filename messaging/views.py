from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.contrib import messages
from .models import Thread, Message
from .encryption import encrypt_message, decrypt_message
from accounts.models import User

@login_required
def inbox_view(request):
    """ Shows all active conversations for the logged-in user. """
    threads = request.user.threads.filter(is_active=True).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')
    
    # We will pass the threads to the template, the template will use get_other_participant
    return render(request, 'messaging/inbox.html', {'threads': threads})

@login_required
def thread_detail_view(request, thread_id):
    """ View a single conversation and handle sending new messages. """
    thread = get_object_or_404(Thread, pk=thread_id, participants=request.user)
    
    # Handle incoming new encrypted message
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            # ENCRYPT before saving to database
            encrypted_bytes = encrypt_message(content)
            new_msg = Message(
                thread=thread,
                sender=request.user,
                encrypted_content=encrypted_bytes
            )
            
            # PKI Digital Signature
            raw_password = request.session.get('pki_passphrase', '')
            if request.user.private_key_encrypted and raw_password:
                import base64
                from cryptography.hazmat.primitives.asymmetric import padding
                from cryptography.hazmat.primitives import hashes, serialization
                from cryptography.hazmat.backends import default_backend
                try:
                    private_key_bytes = request.user.private_key_encrypted.encode('utf-8')
                    private_key = serialization.load_pem_private_key(
                        private_key_bytes, password=raw_password.encode(), backend=default_backend()
                    )
                    signature = private_key.sign(content.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
                    new_msg.cryptographic_signature = base64.b64encode(signature).decode('utf-8')
                except Exception:
                    pass
            
            new_msg.save()
            # Update thread updated_at
            thread.save()
            return redirect('thread_detail', thread_id=thread.id)
            
    # Fetch all messages in this thread
    db_messages = thread.messages.all()
    
    # Decrypt them in memory for the template
    chat_history = []
    for msg in db_messages:
        # Mark as read if the current user isn't the sender
        if not msg.is_read and msg.sender != request.user:
            msg.is_read = True
            msg.save()
            
        chat_history.append({
            'sender': msg.sender,
            'is_me': msg.sender == request.user,
            'text': decrypt_message(msg.encrypted_content),
            'created_at': msg.created_at,
            'signature': msg.cryptographic_signature
        })
        
    other_user = thread.get_other_participant(request.user)
    
    return render(request, 'messaging/thread.html', {
        'thread': thread,
        'chat_history': chat_history,
        'other_user': other_user
    })

@login_required
def start_conversation(request, user_id):
    """ Starts or resumes a conversation with a specific user. """
    target_user = get_object_or_404(User, pk=user_id)
    
    if target_user == request.user:
        messages.error(request, "You cannot message yourself.")
        return redirect('inbox')
        
    # Check if a thread already exists between these exactly two users
    # A bit complex in ManyToMany, so we filter threads where BOTH are participants
    existing_thread = Thread.objects.filter(participants=request.user).filter(participants=target_user).first()
    
    if existing_thread:
        return redirect('thread_detail', thread_id=existing_thread.id)
        
    # Create a new thread
    new_thread = Thread.objects.create()
    new_thread.participants.add(request.user, target_user)
    
    messages.success(request, f"New encrypted channel opened with {target_user.first_name or target_user.email}")
    return redirect('thread_detail', thread_id=new_thread.id)

@login_required
def create_group_chat(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name', '').strip() or 'Unnamed Group'
        emails_raw = request.POST.get('emails', '')
        
        emails = [e.strip() for e in emails_raw.split(',') if e.strip()]
        if not emails:
            messages.error(request, 'Please provide at least one valid email address.')
            return redirect('inbox')
            
        users = list(User.objects.filter(email__in=emails))
        
        if not users:
            messages.error(request, 'None of those email addresses belong to registered users.')
            return redirect('inbox')
            
        thread = Thread.objects.create(group_name=group_name)
        thread.participants.add(request.user, *users)
        
        messages.success(request, f"Created group chat '{group_name}'!")
        return redirect('thread_detail', thread_id=thread.id)
        
    return redirect('inbox')
