from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from tagging.fields import TagField
from markdown import markdown
import datetime

class Category(models.Model):
    title = models.CharField(max_length=250, help_text="maximum 250 Characters.")
    slug = models.SlugField(unique=True, help_text="Suggested value automatically genarated from title. Must be unique")
    description = models.TextField()
    
    class Meta:
        ordering = ['title']
        verbose_name_plural="Categories"

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return "/categories/%s/" % self.slug

    def live_entry_set(self):
        from coltrane.models import Entry
        return self.entry_set.filter(status=Entry.LIVE_STATUS)

#-------------------------------------Entry Model----------------------------------------

class LiveEntryManager(models.Manager):
    def get_query_set(self):
        return super(LiveEntryModel,self).get_query_set().filter(status=self.model.LIVE_STATUS)

class Entry(models.Model):
    LIVE_STATUS=1
    DRAFT_STATUS=2
    HIDDEN_STATUS=3
    STATUS_CHOICES=(
        (LIVE_STATUS,'Live'),
        (DRAFT_STATUS,'Draft'),
        (HIDDEN_STATUS,'Hidden'))
    
    title=models.CharField(max_length=250)
    excerpt=models.TextField(blank=True)
    body=models.TextField()
    pub_date=models.DateTimeField(default=datetime.datetime.now)
    
    author=models.ForeignKey(User)
    enable_comments=models.BooleanField(default=False)
    feature=models.BooleanField(default=False)
    slug=models.SlugField(unique_for_date='pub_date')
    status=models.IntegerField(choices=STATUS_CHOICES,default=LIVE_STATUS)

    excerpt_html=models.TextField(editable=False,blank=True)
    body_html=models.TextField(editable=False,blank=True)

    categories=models.ManyToManyField(Category)
    tags=TagField()
    
    live = LiveEntryManager()
    objects = models.Manager()

    def save(self,force_insert=False,force_update=False):
        self.body_html=markdown(self.body)
        if self.excerpt:
            self.excerpt_html=markdown(self.excerpt)
        super(Entry,self).save(force_insert,force_update)
        
    class Meta:
        verbose_name_plural="Entries"
        ordering = ['-pub_date']

    def __unicode__(self):
        return self.title
    
    @models.permalink
    def get_absolute_url(self):
        return ('coltrane_entry_detail',(),{'year': self.pub_date.strftime("%Y"),
                                            'month': self.pub_date.strftime("%b").lower(),
                                            'day': self.pub_date.strftime("%d"),
                                            'slug': self.slug })
#    get_absolute_url=models.permalink(get_absolute_url)

        #"/weblog/%s/%s/" % (self.pub_date.strftime("%Y/%b/%d").lower(),self.slug)


#--------------------------------Link Model-----------------------------------------------

class Link(models.Model):
    title=models.CharField(max_length=250)
    description=models.TextField(blank=True)
    description_html=models.TextField(blank=True)
    url=models.URLField(unique=True)

    posted_by=models.ForeignKey(User)
    pub_date=models.DateTimeField(default=datetime.datetime.now)
    slug=models.SlugField(unique_for_date='pub_date')

    tags=TagField()

    enable_comments=models.BooleanField(default=True)
    post_elsewhere=models.BooleanField('Post to Delicious',default=True)

    via_name=models.CharField('Via',max_length=250,blank=True,help_text='The name of person whose site you spotted the link on.Optional.')
    via_url=models.URLField('Via URL',verify_exists=False,blank=True,help_text='The url of the site where you spotted the link. Optional.')


    class Meta:
        ordering=['-pub_date']

    def __unicode__(self):
        return self.title

    def save(self):
        if self.description:
            self.description_html=markdown(self.description)
        if not self.id and self.post_elsewhere:
            import pydelicious
            from django.utils.encoding import smart_str
            pydelicious.add(settings.DELICIOUS_USER,settings.DELICIOUS_PASSWORD,
                            smart_str(self.url),smart_str(self.title),smart_str(self.tags))
        super(Link,self).save()
    
    @models.permalink
    def get_absolute_url(self):
        return ('coltrane_link_detail',(),{'year':self.pub_date.strftime('%Y'),
                                           'month':self.pub_date.strftime('%b').lower(),
                                           'day':self.pub_date.strftime('%d'),
                                           'slug':self.slug})
