# Generated by Django 5.2.3 on 2025-07-05 09:23

from django.db import migrations, models


class Migration(migrations.Migration):
	dependencies = [
		('testcase', '0003_alter_testcaserun_browser_session_and_more'),
	]

	operations = [
		migrations.AddField(
			model_name='testcaserun',
			name='name',
			field=models.TextField(blank=True, null=True),
		),
		migrations.AddField(
			model_name='testcaserun',
			name='priority',
			field=models.CharField(
				blank=True,
				choices=[
					('Critical', 'Critical'),
					('High', 'High'),
					('Medium', 'Medium'),
					('Low', 'Low'),
				],
				max_length=20,
				null=True,
			),
		),
		migrations.AlterField(
			model_name='testcaserun',
			name='name',
			field=models.TextField(),
		),
		migrations.AlterField(
			model_name='testcaserun',
			name='priority',
			field=models.CharField(
				choices=[
					('Critical', 'Critical'),
					('High', 'High'),
					('Medium', 'Medium'),
					('Low', 'Low'),
				],
				max_length=20,
			),
		),
	]
