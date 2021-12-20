from django.db import models

# Create your models here.

class ProtectedResource(models.Model):
    # Handling choices below due to http://www.b-list.org/weblog/2007/nov/02/handle-choices-right-way/
    URL = 'URL'
    PDF = 'PDF'
    DOC = 'DOC'
    DOCX = 'DOCX'
    PPTX = 'PPTX'
    TXT = 'TXT'
    RESOURCE_TYPES = (
        (URL, 'Website address'),
        (PDF, 'PDF file'),
        (DOC, 'Word document, old format'),
        (DOCX, 'Word document, new format'),
        (PPTX, 'Powerpoint presentation'),
        (TXT, 'Standard text file'),
    )

    A = 'A'
    N = 'N'
    S = 'S'
    F = 'F'
    P = 'P'
    O = 'O'
    I = 'I'
    STATUS_TYPES = (
        (A, 'Active'),
        (N, 'Newly placed order'),
        (S, 'Being scanned'),
        (F, 'Last scan failed'),
        (P, 'Awaiting payment'),
        (I, 'Inactive'),
    )

    DAILY = 86400
    WEEKLY = 604800
    MONTHLY = 2592000
    SCAN_FREQUENCY = (
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
    )

    url = models.CharField(max_length=2048, blank=True)
    file = models.FileField(upload_to='userfiles/%Y/%m/%d', blank=True)
    type = models.CharField(max_length=4, choices=RESOURCE_TYPES, default=URL)
    status = models.CharField(max_length=1, choices=STATUS_TYPES, default=A)
    scan_frequency = models.PositiveIntegerField(choices=SCAN_FREQUENCY,
                                                 default=WEEKLY)
    original_filename = models.CharField(max_length=260, null=True, blank=True)  # If type not URL

    def __str__(self):
        return str(self.id) + ': ' + self.type

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension

    def clean(self):
        # Either URL or File must be entered
        if self.url is None and self.file is None:
            raise ValidationError('URL or file required')


class Query(models.Model):
    query = models.CharField(max_length=250)

    def __str__(self):
        return str(self.id) + ': ' + self.query

class ScanLog(models.Model):
    H = 'H'
    C = 'C'
    FAILED_TYPE = (
        (H, 'HTTP error'),
        (C, 'No content candidates found (initial scan) or matched (post processing)'),
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    queries = models.ManyToManyField(Query, blank=True)
    protected_resource = models.CharField(max_length=10000000, blank=True)
    fail_reason = models.CharField(max_length=500, null=True, blank=True)
    fail_type = models.CharField(max_length=1, choices=FAILED_TYPE, null=True, blank=True)

    def __str__(self):
        return str(self.id) + ': ' + self.timestamp.strftime("%b %d %Y %H:%M:%S")


class ScanResult(models.Model):
    result_log = models.ForeignKey(ScanLog, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    match_url = models.CharField(max_length=2048)
    match_display_url = models.CharField(max_length=2048)
    post_scanned = models.BooleanField(default=False)
    post_fail_reason = models.CharField(max_length=500, null=True, blank=True)
    post_fail_type = models.CharField(max_length=1, choices=ScanLog.FAILED_TYPE, null=True, blank=True)
    perc_of_duplication = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # NNN.DD%

    def __str__(self):
        return str(self.id) + ': ' + f"{self.perc_of_duplication}"
