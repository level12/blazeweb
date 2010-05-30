
class Action(object):
    def perform():
        pass
    
    def __call__(self, *args, **kwargs):
        return self.perform(*args, **kwargs)