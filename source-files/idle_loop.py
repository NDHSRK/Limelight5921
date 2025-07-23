# runPipeline() is called every frame by Limelight's backend.
def runPipeline(image, llrobot):
    return [[]], image, [
                400, # SampleRecognition.SampleRecognitionReturn.RecognitionStatus.IDLE.value
                3] # SampleRecord.SampleColor.NONE.value
