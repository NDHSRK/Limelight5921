package org.firstinspires.ftc.teamcode.auto.opmodes.limelightauto;

import com.qualcomm.hardware.limelightvision.LLResult;
import com.qualcomm.hardware.limelightvision.LLStatus;
import com.qualcomm.hardware.limelightvision.Limelight3A;
import com.qualcomm.robotcore.eventloop.opmode.Autonomous;
import com.qualcomm.robotcore.eventloop.opmode.LinearOpMode;
import com.qualcomm.robotcore.util.ElapsedTime;
import com.qualcomm.robotcore.util.RobotLog;

import org.firstinspires.ftc.robotcore.external.navigation.Pose3D;
import org.firstinspires.ftc.teamcode.auto.opmodes.limelightauto.utils.Pair;
import org.firstinspires.ftc.teamcode.auto.opmodes.limelightauto.utils.TimeStamp;

import java.util.Date;

/*
 * This OpMode illustrates how to use the Limelight3A Vision Sensor.
 *
 * @see <a href="https://limelightvision.io/">Limelight</a>
 *
 * Notes on configuration:
 *
 *   The device presents itself, when plugged into a USB port on a Control Hub as an ethernet
 *   interface.  A DHCP server running on the Limelight automatically assigns the Control Hub an
 *   ip address for the new ethernet interface.
 *
 *   Since the Limelight is plugged into a USB port, it will be listed on the top level configuration
 *   activity along with the Control Hub Portal and other USB devices such as webcams.  Typically
 *   serial numbers are displayed below the device's names.  In the case of the Limelight device, the
 *   Control Hub's assigned ip address for that ethernet interface is used as the "serial number".
 *
 *   Tapping the Limelight's name, transitions to a new screen where the user can rename the Limelight
 *   and specify the Limelight's ip address.  Users should take care not to confuse the ip address of
 *   the Limelight itself, which can be configured through the Limelight settings page via a web browser,
 *   and the ip address the Limelight device assigned the Control Hub and which is displayed in small text
 *   below the name of the Limelight on the top level configuration screen.
 */
@Autonomous(name = "CustomLimelight3A", group = "TeamCode")
//@Disabled
public class CustomLimelight3A extends LinearOpMode {
    private static final String TAG = CustomLimelight3A.class.getSimpleName();

    public enum Alliance {
        NONE, BLUE, RED
    }

    public enum SampleColor {
        BLUE, RED, YELLOW, NPOS
    }

    private Limelight3A limelight;

    @Override
    public void runOpMode() throws InterruptedException
    {
        limelight = hardwareMap.get(Limelight3A.class, "limelight");
        if (!initializeLimelight())
            throw new RuntimeException(TAG + " Limelight failed to initialize");

        telemetry.addData(">", "Limelight Ready.  Press Play.");
        telemetry.update();
        waitForStart();

        // Derived from Team 4348 IntoTheDeep FTCAuto case "LIMELIGHT_HANDHELD": {
        Pair<Boolean, LimelightReturn> recognitionResults = recognizeSample(Alliance.RED);
        if (!recognitionResults.first)
            RobotLog.dd(TAG, "Limelight timed out during recognition or failed to find a sample to pick up");

        limelight.stop();
    }

    // Common method for initializing the Limelight to the idle
    // pipeline 1. Returns false if we timed out waiting for the
    // Limelight to initialize.
    boolean initializeLimelight() {
        // Check that the Limelight camera has been configured in.
        if (limelight == null)
            throw new RuntimeException(TAG + " The Limelight camera is not in the configuration");

        // Don't do this, it returns false -- if (!robot.limelight.isConnected())
        //    throw new AutonomousRobotException(TAG, "The Limelight camera is not connected");

        telemetry.setAutoClear(true);

        RobotLog.ii(TAG, "Setting up the Limelight camera for pipeline 1 (idle)");
        limelight.pipelineSwitch(1);
        double[] llIdle = {0.0};
        limelight.updatePythonInputs(llIdle);

        limelight.start();
        sleep(500);

        int numNoStatusCycles = 0;
        int numNullResultsCycles = 0;
        int numNoOutputCycles = 0;

        boolean retVal = true; // default
        ElapsedTime limelightInitTimer = new ElapsedTime(ElapsedTime.Resolution.MILLISECONDS);
        limelightInitTimer.reset(); // start the limelightInitTimer

        //!! WARNING - if you call initializeLimelight() between
        // runOpMode() and waitForStart(), you *must* not test
        // opModeIsActive() because it only returns true after
        // after the driver hits the play button, i.e. *after*
        // waitForStart.
        while (!isStopRequested()) {
            if (limelightInitTimer.milliseconds() >= 1000) {
                retVal = false;
                telemetry.addLine("Limelight timed out during initialization");
                telemetry.update();
                RobotLog.dd(TAG, "Limelight timed out during initialization");
                break;
            }

            LLStatus status = limelight.getStatus();
            if (status == null || status.getFps() == 0.0) {
                numNoStatusCycles++;
                continue;
            }

            LLResult result = limelight.getLatestResult();
            if (result == null) {
                numNullResultsCycles++;
                continue;
            }

            if (result.isValid()) {
                telemetry.addData("tx", result.getTx());
                telemetry.addData("txnc", result.getTxNC());
                telemetry.addData("ty", result.getTy());
                telemetry.addData("tync", result.getTyNC());
                Pose3D botpose = result.getBotpose();
                telemetry.addData("Botpose", botpose.toString());
            }

            double[] pythonOutputs = result.getPythonOutput();
            if (pythonOutputs == null || pythonOutputs.length == 0) {
                numNoOutputCycles++;
                continue;
            }

            // Got some kind of results from the Limelight.
            LimelightReturn llRetVal = new LimelightReturn(pythonOutputs);
            if (llRetVal.statusCode == LimelightReturn.LIMELIGHT_IDLE_LOOP) {
                telemetry.addLine("Limelight is initialized and returning results for pipeline 1 (idle)");
                telemetry.update();
                RobotLog.dd(TAG, "Limelight is initialized and returning results for pipeline 1 (idle)");
                break;
            }
        }

        RobotLog.dd(TAG, "Number of no status cycles " + numNoStatusCycles +
                ", null results cycles " + numNullResultsCycles + ", no output cycles " + numNoOutputCycles);
        return retVal;
    }

    // Return value is Pair<Boolean, LimelightReturn> where if the Boolean is false, LimelightReturn is null
    private Pair<Boolean, LimelightReturn> recognizeSample(Alliance pAlliance) {
        // Switch to the alliance pipeline.
        RobotLog.ii(TAG, "Switching the Limelight camera to sample recognition pipeline 0");
        limelight.pipelineSwitch(0);

        RobotLog.ii(TAG, "Run the Limelight for alliance " + pAlliance + " with ordinal " + pAlliance.ordinal());
        double[] llRobot = {(double) pAlliance.ordinal()};
        limelight.updatePythonInputs(llRobot);

        boolean successfulLimelightRecognition = false;
        LimelightReturn retVal = null;

        int numNullResultsCycles = 0;
        int numNoOutputCycles = 0;
        int numIdleLoopCycles = 0;
        int numImageNotAvailable = 0;

        ElapsedTime limelightResultsTimer = new ElapsedTime(ElapsedTime.Resolution.MILLISECONDS);
        limelightResultsTimer.reset(); // start the timer
        while (opModeIsActive()) {

            if (limelightResultsTimer.milliseconds() >= 1000) {
                telemetry.addLine("Limelight timed out while processing");
                telemetry.update();
                RobotLog.dd(TAG, "Limelight timed out while processing");
                break;
            }

            LLResult result = limelight.getLatestResult();
            if (result == null) {
                numNullResultsCycles++;
                continue;
            }

            double[] pythonOutputs = result.getPythonOutput();
            if (pythonOutputs == null || pythonOutputs.length == 0) {
                numNoOutputCycles++;
                continue;
            }

            // Got some kind of results from the Limelight.
            retVal = new LimelightReturn(pythonOutputs);
            if (retVal.statusCode == LimelightReturn.LIMELIGHT_IDLE_LOOP) {
                numIdleLoopCycles++;
                continue;
            }

            // If we've switched pipelines but the Limelight has not yet
            // delivered a valid image to our script, just keep going,
            // although you may time out.
            if (retVal.statusCode == LimelightReturn.IMAGE_NOT_AVAILABLE) {
                numImageNotAvailable++;
                RobotLog.dd(TAG, "Pipeline was called but no image was available");
                continue;
            }

            if (retVal.statusCode == LimelightReturn.PYTHON_APP_CRASH) {
                String crashTimestamp = "LRC_" + TimeStamp.getDateTimeStamp(new Date());
                retVal.logLimelightReturn(pAlliance, crashTimestamp);
                break;
            }

            // Got actual results for the selected alliance.
            if (retVal.statusCode == LimelightReturn.RECOGNITION_FAILURE) {
                String snapshotTimestamp = "LRF_" + TimeStamp.getDateTimeStamp(new Date());
                limelight.captureSnapshot(snapshotTimestamp);

                telemetry.addLine("Recognition failure");
                telemetry.update();
                RobotLog.dd(TAG, "Saving snapshot from recognition failure on the Limelight " + snapshotTimestamp);
                RobotLog.dd(TAG, "Recognition failure");

                retVal.logLimelightReturn(pAlliance, snapshotTimestamp);
                break;
            }

            // Make sure the status code is SUCCESS - but don't crash if it's not.
            if (retVal.statusCode != LimelightReturn.RECOGNITION_SUCCESS) {
                RobotLog.dd(TAG, "Got " + retVal.statusCode + " instead of the expected success code");
                break;
            }

            successfulLimelightRecognition = true;
            String snapshotTimestamp = "LRS_" + TimeStamp.getDateTimeStamp(new Date());
            limelight.captureSnapshot(snapshotTimestamp);

            telemetry.addLine("Limelight recognition successful");
            telemetry.update();
            RobotLog.dd(TAG, "Limelight recognition successful");
            RobotLog.dd(TAG, "Saving snapshot on the Limelight " + snapshotTimestamp);

            retVal.logLimelightReturn(pAlliance, snapshotTimestamp);
            break;
        } // while

        RobotLog.dd(TAG, "Number of null results cycles " + numNullResultsCycles +
                ", Number of no output cycles " + numNoOutputCycles);
        RobotLog.dd(TAG, "Number of idle loop cycles " + numIdleLoopCycles +
                ", Number of no image cycles " + numImageNotAvailable);

        // Switch back to the idle pipeline.
        RobotLog.ii(TAG, "Resetting the Limelight camera to pipeline 1 (idle)");
        double[] llIdle = {0.0}; // alliance NONE
        limelight.updatePythonInputs(llIdle);
        limelight.pipelineSwitch(1);

        return Pair.create(successfulLimelightRecognition, retVal);
    }

    private static class LimelightReturn {

        private static final int STATUS_CODE_INDEX = 0;
        public static final int RECOGNITION_SUCCESS = 200; // from http
        public static final int PYTHON_APP_CRASH = 300; // Python application crash
        public static final int LIMELIGHT_IDLE_LOOP = 400;
        public static final int IMAGE_NOT_AVAILABLE = 450;
        public static final int RECOGNITION_FAILURE = 500; // from http
        public final int statusCode;

        private static final int PYTHON_APP_CRASH_LINE_NUMBER_INDEX = 1; // overlaps selected color index below
        public int pythonAppCrashLineNumber;

        // Success and failure.
        private static final int SELECTED_SAMPLE_COLOR_INDEX = 1;
        public SampleColor selectedSampleColor;

        // Success only.
        private static final int FTC_ANGLE_INDEX = 2;
        public double ftcAngle;
        private static final int SELECTED_SAMPLE_CENTER_X_INDEX = 3;
        public int selectedSampleCenterX; // pixels
        private static final int SELECTED_SAMPLE_CENTER_Y_INDEX = 4;
        public int selectedSampleCenterY; // pixels

        // Decode the anonymous array that our application returns from the Limelight.
        public LimelightReturn(double[] llPython) {

            statusCode = (int) llPython[STATUS_CODE_INDEX]; // all paths

            if (statusCode == PYTHON_APP_CRASH) {
                pythonAppCrashLineNumber = (int) llPython[PYTHON_APP_CRASH_LINE_NUMBER_INDEX];
                return;
            }

            if (!(statusCode == RECOGNITION_SUCCESS || statusCode == RECOGNITION_FAILURE))
                return;

            RobotLog.dd(TAG, "Limelight success or failure: extracting fields");

            int colorIndexOrdinal = (int) llPython[SELECTED_SAMPLE_COLOR_INDEX];
            selectedSampleColor = SampleColor.values()[colorIndexOrdinal];

            if (statusCode == RECOGNITION_SUCCESS) {
                ftcAngle = llPython[FTC_ANGLE_INDEX];
                selectedSampleCenterX = (int) llPython[SELECTED_SAMPLE_CENTER_X_INDEX];
                selectedSampleCenterY = (int) llPython[SELECTED_SAMPLE_CENTER_Y_INDEX];
            }
        }

        public void logLimelightReturn(Alliance pAlliance, String pTimestamp) {
            if (!(statusCode == PYTHON_APP_CRASH ||
                    statusCode == RECOGNITION_SUCCESS || statusCode == RECOGNITION_FAILURE))
                return;

            RobotLog.dd(TAG, "Logging Limelight return for alliance " + pAlliance +
                    ", timestamp " + pTimestamp);
            RobotLog.dd(TAG, "Return status " + statusCode);

            if (statusCode == PYTHON_APP_CRASH) {
                RobotLog.dd(TAG, "The Python app on the Limelight crashed at line " + pythonAppCrashLineNumber);
                return;
            }

            RobotLog.dd(TAG, "Limelight: selected sample color " + selectedSampleColor);

            if (statusCode == RECOGNITION_SUCCESS)
                RobotLog.dd(TAG, "Selected sample FTC angle " +  ftcAngle +
                            ", center x " + selectedSampleCenterX + ", y " + selectedSampleCenterY);
       }
    }

}
