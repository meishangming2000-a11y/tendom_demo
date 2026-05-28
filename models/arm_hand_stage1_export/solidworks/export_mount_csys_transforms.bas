Attribute VB_Name = "export_mount_csys_transforms"
Option Explicit

' Export named SolidWorks coordinate systems to a CSV file.
'
' How to use:
'   1. Open the arm assembly in SolidWorks and run this macro.
'   2. Open the hand assembly in SolidWorks and run this macro again.
'   3. Send/import the generated CSV files.
'
' Output:
'   A CSV next to the active SolidWorks document, named:
'     <assembly-name>_mount_csys_export.csv
'
' Notes:
'   - SolidWorks internal length unit is meter.
'   - The macro exports origin and transformed unit axes in the active
'     document coordinate frame.
'   - It tries canonical names plus one common typo seen in screenshots.

Private Function VecLen(ByVal x As Double, ByVal y As Double, ByVal z As Double) As Double
    VecLen = Sqr(x * x + y * y + z * z)
End Function

Private Sub NormalizeVec(ByRef x As Double, ByRef y As Double, ByRef z As Double)
    Dim n As Double
    n = VecLen(x, y, z)
    If n > 0# Then
        x = x / n
        y = y / n
        z = z / n
    End If
End Sub

Private Function PointArray(ByVal x As Double, ByVal y As Double, ByVal z As Double) As Variant
    Dim a(2) As Double
    a(0) = x
    a(1) = y
    a(2) = z
    PointArray = a
End Function

Private Function CsvNum(ByVal value As Double) As String
    CsvNum = Replace(Format$(value, "0.000000000000"), ",", ".")
End Function

Private Sub WriteCsysRow(ByVal fnum As Integer, ByVal swApp As SldWorks.SldWorks, ByVal swModel As SldWorks.ModelDoc2, ByVal csysName As String)
    On Error GoTo ExportFailed

    Dim swMathUtil As SldWorks.MathUtility
    Dim swTransform As SldWorks.MathTransform
    Set swMathUtil = swApp.GetMathUtility
    Set swTransform = swModel.Extension.GetCoordinateSystemTransformByName(csysName)

    If swTransform Is Nothing Then
        Print #fnum, csysName & ",MISSING,,,,,,,,,,,,,,,,,,,"
        Exit Sub
    End If

    Dim p0 As SldWorks.MathPoint
    Dim px As SldWorks.MathPoint
    Dim py As SldWorks.MathPoint
    Dim pz As SldWorks.MathPoint
    Set p0 = swMathUtil.CreatePoint(PointArray(0#, 0#, 0#)).MultiplyTransform(swTransform)
    Set px = swMathUtil.CreatePoint(PointArray(1#, 0#, 0#)).MultiplyTransform(swTransform)
    Set py = swMathUtil.CreatePoint(PointArray(0#, 1#, 0#)).MultiplyTransform(swTransform)
    Set pz = swMathUtil.CreatePoint(PointArray(0#, 0#, 1#)).MultiplyTransform(swTransform)

    Dim o As Variant
    Dim xpt As Variant
    Dim ypt As Variant
    Dim zpt As Variant
    o = p0.ArrayData
    xpt = px.ArrayData
    ypt = py.ArrayData
    zpt = pz.ArrayData

    Dim xx As Double, xy As Double, xz As Double
    Dim yx As Double, yy As Double, yz As Double
    Dim zx As Double, zy As Double, zz As Double
    xx = CDbl(xpt(0)) - CDbl(o(0))
    xy = CDbl(xpt(1)) - CDbl(o(1))
    xz = CDbl(xpt(2)) - CDbl(o(2))
    yx = CDbl(ypt(0)) - CDbl(o(0))
    yy = CDbl(ypt(1)) - CDbl(o(1))
    yz = CDbl(ypt(2)) - CDbl(o(2))
    zx = CDbl(zpt(0)) - CDbl(o(0))
    zy = CDbl(zpt(1)) - CDbl(o(1))
    zz = CDbl(zpt(2)) - CDbl(o(2))
    NormalizeVec xx, xy, xz
    NormalizeVec yx, yy, yz
    NormalizeVec zx, zy, zz

    Dim arr As Variant
    arr = swTransform.ArrayData

    Print #fnum, _
        csysName & ",FOUND," & _
        CsvNum(CDbl(o(0))) & "," & CsvNum(CDbl(o(1))) & "," & CsvNum(CDbl(o(2))) & "," & _
        CsvNum(xx) & "," & CsvNum(xy) & "," & CsvNum(xz) & "," & _
        CsvNum(yx) & "," & CsvNum(yy) & "," & CsvNum(yz) & "," & _
        CsvNum(zx) & "," & CsvNum(zy) & "," & CsvNum(zz) & "," & _
        CsvNum(CDbl(o(0)) * 1000#) & "," & CsvNum(CDbl(o(1)) * 1000#) & "," & CsvNum(CDbl(o(2)) * 1000#) & "," & _
        CsvNum(CDbl(arr(0))) & "," & CsvNum(CDbl(arr(1))) & "," & CsvNum(CDbl(arr(2))) & "," & _
        CsvNum(CDbl(arr(3))) & "," & CsvNum(CDbl(arr(4))) & "," & CsvNum(CDbl(arr(5))) & "," & _
        CsvNum(CDbl(arr(6))) & "," & CsvNum(CDbl(arr(7))) & "," & CsvNum(CDbl(arr(8))) & "," & _
        CsvNum(CDbl(arr(9))) & "," & CsvNum(CDbl(arr(10))) & "," & CsvNum(CDbl(arr(11)))
    Exit Sub

ExportFailed:
    Print #fnum, csysName & ",ERROR," & Replace(Err.Description, ",", ";")
    Err.Clear
End Sub

Private Sub WriteMountLikeFeatureRows(ByVal fnum As Integer, ByVal swApp As SldWorks.SldWorks, ByVal swModel As SldWorks.ModelDoc2)
    Dim feat As SldWorks.Feature
    Set feat = swModel.FirstFeature
    Do While Not feat Is Nothing
        Dim nm As String
        nm = feat.Name
        If InStr(1, LCase$(nm), "mount", vbTextCompare) > 0 Or _
           InStr(1, LCase$(nm), "flange", vbTextCompare) > 0 Or _
           InStr(1, LCase$(nm), "wrist", vbTextCompare) > 0 Then
            WriteCsysRow fnum, swApp, swModel, nm
        End If
        Set feat = feat.GetNextFeature
    Loop
End Sub

Private Sub WriteExplicitBridgeRows(ByVal fnum As Integer, ByVal swApp As SldWorks.SldWorks, ByVal swModel As SldWorks.ModelDoc2)
    ' These are the coordinate systems needed to map CAD mount frames into
    ' the already-converted MuJoCo body frames.
    WriteCsysRow fnum, swApp, swModel, "csys_base"
    WriteCsysRow fnum, swApp, swModel, "csys_j1"
    WriteCsysRow fnum, swApp, swModel, "csys_j2"
    WriteCsysRow fnum, swApp, swModel, "csys_j3"
    WriteCsysRow fnum, swApp, swModel, "csys_j4"
    WriteCsysRow fnum, swApp, swModel, "ee_tool_frame"
    WriteCsysRow fnum, swApp, swModel, "csys_ee_mount"
    WriteCsysRow fnum, swApp, swModel, "hand_base_csys"
    WriteCsysRow fnum, swApp, swModel, "wrist_bottom_csys"
    WriteCsysRow fnum, swApp, swModel, "wrist_1_csys"
    WriteCsysRow fnum, swApp, swModel, "wrist_2_csys"
End Sub

Sub main()
    Dim swApp As SldWorks.SldWorks
    Dim swModel As SldWorks.ModelDoc2
    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc

    If swModel Is Nothing Then
        MsgBox "No active SolidWorks document."
        Exit Sub
    End If

    Dim docPath As String
    docPath = swModel.GetPathName
    Dim outPath As String
    If Len(docPath) > 0 Then
        Dim folder As String
        Dim base As String
        folder = Left$(docPath, InStrRev(docPath, "\"))
        base = Mid$(docPath, InStrRev(docPath, "\") + 1)
        If InStrRev(base, ".") > 0 Then base = Left$(base, InStrRev(base, ".") - 1)
        outPath = folder & base & "_mount_csys_export.csv"
    Else
        outPath = Environ$("TEMP") & "\solidworks_mount_csys_export.csv"
    End If

    Dim fnum As Integer
    fnum = FreeFile
    Open outPath For Output As #fnum
    Print #fnum, "name,status,origin_x_m,origin_y_m,origin_z_m,x_axis_x,x_axis_y,x_axis_z,y_axis_x,y_axis_y,y_axis_z,z_axis_x,z_axis_y,z_axis_z,origin_x_mm,origin_y_mm,origin_z_mm,raw_m0,raw_m1,raw_m2,raw_m3,raw_m4,raw_m5,raw_m6,raw_m7,raw_m8,raw_m9,raw_m10,raw_m11"

    WriteCsysRow fnum, swApp, swModel, "arm_flange_mount_csys"
    WriteCsysRow fnum, swApp, swModel, "hand_wrist_mount_csys"
    WriteCsysRow fnum, swApp, swModel, "hand_wrist_mount_cysc"
    WriteExplicitBridgeRows fnum, swApp, swModel
    WriteMountLikeFeatureRows fnum, swApp, swModel

    Close #fnum
    MsgBox "Mount coordinate-system CSV exported:" & vbCrLf & outPath
End Sub
