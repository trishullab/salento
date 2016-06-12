/* Author: Vijay Murali */

package driver;

import java.util.List;

/** Configurable options for the driver */
public final class Options
{
    private Options() { }

    /** Maximum number of sequences from components */
    public static final int MAX_SEQS = 100;

    /** maximum length of sequence */
    public static final int MAX_LEN = 1000;

    /** validate each sequence before it's printed (by calling hasValidHistory()).
     * true by default */
    public static boolean validateSequences = true;

    /** print branch events */
    public static boolean printBranches = false;

    /** print location info with each event? */
    public static boolean printLocation = false;

    /** print in JSON or old format */
    public static boolean printJSON = false;

    /** print START and END indicators for each sequence? */
    public static boolean printSequenceStartEnd = false;

    /** type of unit graph to generate ("brief"/"trap"). default is brief */
    public static String unitGraph = "brief";

    /** Type states that we're interested in getting sequences on */
    public static List<String> relevantTypestates;

    /** obey Android entry points (below). true by default.
     * If false sequences will be extracted starting from every soot method */
    public static boolean obeyAndroidEntryPoints = true;

    /** Android entry points */
    public static String[] androidEntryPoints =
        {
            /* Activity public methods */
            "android.app.Activity.onActionModeFinished",
            "android.app.Activity.onActionModeStarted",
            "android.app.Activity.onActivityReenter",
            "android.app.Activity.onAttachFragment",
            "android.app.Activity.onAttachedToWindow",
            "android.app.Activity.onBackPressed",
            "android.app.Activity.onConfigurationChanged",
            "android.app.Activity.onContentChanged",
            "android.app.Activity.onContextItemSelected",
            "android.app.Activity.onContextMenuClosed",
            "android.app.Activity.onCreate",
            "android.app.Activity.onCreateContextMenu",
            "android.app.Activity.onCreateDescription",
            "android.app.Activity.onCreateNavigateUpTaskStack",
            "android.app.Activity.onCreateOptionsMenu",
            "android.app.Activity.onCreatePanelMenu",
            "android.app.Activity.onCreatePanelView",
            "android.app.Activity.onCreateThumbnail",
            "android.app.Activity.onCreateView",
            "android.app.Activity.onDetachedFromWindow",
            "android.app.Activity.onEnterAnimationComplete",
            "android.app.Activity.onGenericMotionEvent",
            "android.app.Activity.onKeyDown",
            "android.app.Activity.onKeyLongPress",
            "android.app.Activity.onKeyMultiple",
            "android.app.Activity.onKeyShortcut",
            "android.app.Activity.onKeyUp",
            "android.app.Activity.onLowMemory",
            "android.app.Activity.onMenuItemSelected",
            "android.app.Activity.onMenuOpened",
            "android.app.Activity.onNavigateUp",
            "android.app.Activity.onNavigateUpFromChild",
            "android.app.Activity.onOptionsItemSelected",
            "android.app.Activity.onOptionsMenuClosed",
            "android.app.Activity.onPanelClosed",
            "android.app.Activity.onPostCreate",
            "android.app.Activity.onPrepareNavigateUpTaskStack",
            "android.app.Activity.onPrepareOptionsMenu",
            "android.app.Activity.onPreparePanel",
            "android.app.Activity.onProvideAssistContent",
            "android.app.Activity.onProvideAssistData",
            "android.app.Activity.onProvideReferrer",
            "android.app.Activity.onRequestPermissionsResult",
            "android.app.Activity.onRestoreInstanceState",
            "android.app.Activity.onRetainNonConfigurationInstance",
            "android.app.Activity.onSaveInstanceState",
            "android.app.Activity.onSearchRequested",
            "android.app.Activity.onStateNotSaved",
            "android.app.Activity.onTouchEvent",
            "android.app.Activity.onTrackballEvent",
            "android.app.Activity.onTrimMemory",
            "android.app.Activity.onUserInteraction",
            "android.app.Activity.onVisibleBehindCanceled",
            "android.app.Activity.onWindowAttributesChanged",
            "android.app.Activity.onWindowFocusChanged",
            "android.app.Activity.onWindowStartingActionMode",

            /* Activity protected methods */
            "android.app.Activity.onActivityResult",
            "android.app.Activity.onApplyThemeResource",
            "android.app.Activity.onChildTitleChanged",
            "android.app.Activity.onCreate",
            "android.app.Activity.onCreateDialog",
            "android.app.Activity.onCreateDialog",
            "android.app.Activity.onDestroy",
            "android.app.Activity.onNewIntent",
            "android.app.Activity.onPause",
            "android.app.Activity.onPostCreate",
            "android.app.Activity.onPostResume",
            "android.app.Activity.onPrepareDialog",
            "android.app.Activity.onPrepareDialog",
            "android.app.Activity.onRestart",
            "android.app.Activity.onRestoreInstanceState",
            "android.app.Activity.onResume",
            "android.app.Activity.onSaveInstanceState",
            "android.app.Activity.onStart",
            "android.app.Activity.onStop",
            "android.app.Activity.onTitleChanged",
            "android.app.Activity.onUserLeaveHint",
        };
}
