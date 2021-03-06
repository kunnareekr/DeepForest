import keras

from .evaluation import neonRecall, Jaccard
from keras_retinanet.utils.eval import evaluate

class jaccardCallback(keras.callbacks.Callback):
    """ Evaluation callback for arbitrary datasets.
    """

    def __init__(self, generator, iou_threshold=0.5, score_threshold=0.05, max_detections=100, suppression_threshold=0.2,save_path=None, weighted_average=False, verbose=1,experiment=None,DeepForest_config=None):
        """ Evaluate a given dataset using a given model at the end of every epoch during training.

        # Arguments
            generator       : The generator that represents the dataset to evaluate.
            iou_threshold   : The threshold used to consider when a detection is positive or negative.
            score_threshold : The score confidence threshold to use for detections.
            max_detections  : The maximum number of detections to use per image.
            suppression_threshold:  Percent overlap allowed among boxes
            save_path       : The path to save images with visualized detections to.
            verbose         : Set the verbosity level, by default this is set to 1.
            Experiment   : Comet ml experiment for online logging
        """
        self.generator       = generator
        self.iou_threshold   = iou_threshold
        self.score_threshold = score_threshold
        self.max_detections  = max_detections
        self.suppression_threshold=suppression_threshold
        self.save_path       = save_path
        self.weighted_average = weighted_average
        self.verbose         = verbose
        self.experiment = experiment
        self.DeepForest_config = DeepForest_config

        super(jaccardCallback, self).__init__()
        
    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}

        print("Computing OSBS ground truth IoU")
        jaccard=Jaccard(
            generator=self.generator,
            model=self.model,            
            score_threshold=self.score_threshold,
            save_path=self.save_path,
            experiment=self.experiment,
            DeepForest_config=self.DeepForest_config
        )
        
        print(f" Mean IoU: {jaccard:.2f}")
        
        self.experiment.log_metric("Jaccard", jaccard)               
        
# Neon Recall 
class recallCallback(keras.callbacks.Callback):
    """ Evaluation callback for arbitrary datasets.
    """

    def __init__(self, site,generator, score_threshold=0.05, max_detections=100, suppression_threshold=0.2,save_path=None, weighted_average=False, verbose=1,experiment=None,DeepForest_config=None):
        """ Evaluate a given dataset using a given model at the end of every epoch during training.

        # Arguments
            generator       : The generator that represents the dataset to evaluate.
            iou_threshold   : The threshold used to consider when a detection is positive or negative.
            score_threshold : The score confidence threshold to use for detections.
            max_detections  : The maximum number of detections to use per image.
            suppression_threshold:  Percent overlap allowed among boxes
            save_path       : The path to save images with visualized detections to.
            verbose         : Set the verbosity level, by default this is set to 1.
            Experiment   : Comet ml experiment for online logging
        """
        self.site                = site
        self.generator       = generator
        self.score_threshold = score_threshold
        self.max_detections  = max_detections
        self.suppression_threshold=suppression_threshold
        self.save_path       = save_path
        self.weighted_average = weighted_average
        self.verbose         = verbose
        self.experiment = experiment
        self.DeepForest_config = DeepForest_config

        super(recallCallback, self).__init__()
        
    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}

        print("Computing Recall")
        
        recall=neonRecall(
            self.site,
            self.generator,
            self.model,            
            score_threshold=self.score_threshold,
            save_path=self.save_path,
            max_detections=self.max_detections,
            experiment=self.experiment,
            DeepForest_config=self.DeepForest_config
        )
        
        print(f" Recall: {recall:.2f}")
        
        self.experiment.log_metric("Recall", recall)       


#Hand annotated mAP
class NEONmAP(keras.callbacks.Callback):
    """ Evaluation callback for arbitrary datasets.
    """

    def __init__(self, generator, iou_threshold=0.5, score_threshold=0.05, max_detections=100,save_path=None, weighted_average=False, verbose=1,experiment=None,DeepForest_config=None):
        """ Evaluate a given dataset using a given model at the end of every epoch during training.

        # Arguments
            generator       : The generator that represents the dataset to evaluate.
            iou_threshold   : The threshold used to consider when a detection is positive or negative.
            score_threshold : The score confidence threshold to use for detections.
            max_detections  : The maximum number of detections to use per image.
            save_path       : The path to save images with visualized detections to.
            verbose         : Set the verbosity level, by default this is set to 1.
            Experiment   : Comet ml experiment for online logging
        """
        self.generator       = generator
        self.iou_threshold   = iou_threshold
        self.score_threshold = score_threshold
        self.max_detections  = max_detections
        self.save_path       = save_path
        self.weighted_average = weighted_average
        self.verbose         = verbose
        self.experiment = experiment
        self.DeepForest_config = DeepForest_config

        super(NEONmAP, self).__init__()

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}

        # run evaluation
        average_precisions = evaluate(
            self.generator,
            self.model,
            iou_threshold=self.iou_threshold,
            score_threshold=self.score_threshold,
            max_detections=self.max_detections,
            save_path=self.save_path,
            experiment=self.experiment
        )

        # compute per class average precision
        total_instances = []
        precisions = []
        for label, (average_precision, num_annotations ) in average_precisions.items():
            if self.verbose == 1:
                print('{:.0f} instances of class'.format(num_annotations),
                      self.generator.label_to_name(label), 'with average precision: {:.4f}'.format(average_precision))
            total_instances.append(num_annotations)
            precisions.append(average_precision)
        if self.weighted_average:
            self.mean_neon_ap = sum([a * b for a, b in zip(total_instances, precisions)]) / sum(total_instances)
        else:
            self.mean_neon_ap = sum(precisions) / sum(x > 0 for x in total_instances)

        if self.verbose == 1:
            print('NEON mAP: {:.4f}'.format(self.mean_neon_ap))
        
        self.experiment.log_metric("Neon mAP", self.mean_neon_ap)       
        
