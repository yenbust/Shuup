# Generated by Django 2.2.19 on 2021-06-01 14:04

import django.db.models.deletion
import enumfields.fields
import jsonfield.fields
from django.conf import settings
from django.db import migrations, models

import shuup.core.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shuup', '0090_remove_supplier_module'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackgroundTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('queue', models.CharField(db_index=True, max_length=128, verbose_name='queue name')),
                ('identifier', models.CharField(max_length=128, unique=True, verbose_name='task identifier')),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('modified_on', models.DateTimeField(auto_now=True, verbose_name='modified on')),
                ('function', models.TextField(verbose_name='task function')),
                ('arguments', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='task arguments')),
                ('shop', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='background_tasks', to='shuup.Shop', verbose_name='shop')),
                ('supplier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='background_tasks', to='shuup.Supplier', verbose_name='supplier')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='background_tasks', to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name': 'background task',
                'verbose_name_plural': 'background tasks',
            },
        ),
        migrations.CreateModel(
            name='BackgroundTaskExecution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_on', models.DateTimeField(auto_now_add=True, verbose_name='started on')),
                ('finished_on', models.DateTimeField(null=True, verbose_name='finished on')),
                ('status', enumfields.fields.EnumIntegerField(default=0, enum=shuup.core.models.BackgroundTaskExecutionStatus, verbose_name='status')),
                ('result', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='results')),
                ('error_log', models.TextField(blank=True, null=True, verbose_name='error log')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='shuup.BackgroundTask', verbose_name='background task')),
            ],
            options={
                'verbose_name': 'background task execution',
                'verbose_name_plural': 'background task executions',
            },
        ),
    ]