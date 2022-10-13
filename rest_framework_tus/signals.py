from django.dispatch import Signal

# provide_args=['instance']
receiving = Signal()

# provide_args=['instance']
received = Signal()

# provide_args=['instance']
saving = Signal()

# provide_args=['instance']
saved = Signal()

# provide_args=['instance']
finished = Signal()
