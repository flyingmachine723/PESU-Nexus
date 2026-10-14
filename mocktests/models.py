from django.db import models
from django.contrib.auth.models import User


class Mock_Test(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course_name = models.CharField(max_length=500)
    semester = models.PositiveIntegerField()
    total_qns = models.PositiveIntegerField()
    duration = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class Question(models.Model):
    test = models.ForeignKey(Mock_Test, on_delete=models.CASCADE, related_name='questions')
    question_desc = models.TextField()

    # NEW: optional diagram/image for the question
    question_image = models.ImageField(
        upload_to='question_images/',
        blank=True,
        null=True,
        help_text='Optional. Upload a diagram/image if this question needs one.',
    )

    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=1)
    marks = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Q{self.id} — {self.question_desc[:50]}"


class Test_Attempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Mock_Test, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.test.title}"


class Answer(models.Model):
    attempt = models.ForeignKey(Test_Attempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    selected_answer = models.CharField(max_length=1)

    def __str__(self):
        return f"{self.attempt.user.username} - Question {self.question.id}"