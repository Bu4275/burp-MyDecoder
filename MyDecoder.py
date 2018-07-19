#!-*- coding:utf-8 -*-

from burp import IBurpExtender
from burp import IBurpExtenderCallbacks
from burp import IContextMenuFactory
from burp import IHttpRequestResponse
from burp import IMessageEditorController
from burp import IMessageEditorTabFactory
from burp import ITab
from burp import IMessageEditorTab
from burp import IScannerCheck
from burp import IScanIssue
from burp import IExtensionStateListener
from javax import swing
from java.awt import Font, Color
import re
import sys
import threading
import time
import base64

sysEncodingType = sys.getfilesystemencoding()

class BurpExtender(IBurpExtender, IContextMenuFactory, ITab, IExtensionStateListener):
    TEXTAREA_WIDTH = 650
    TEXTAREA_HEIGHT = 150
    LABEL_WIDTH = 100
    LABEL_HEIGHT = 25

    def registerExtenderCallbacks(self, callbacks):
        self._helpers = callbacks.getHelpers()

        self._jDecoderPanel = swing.JPanel()
        self._jDecoderPanel.setLayout(None)

        # Combobox Values
        self._decodeType = ['Convert to chniese',
                            'Str to Unicode',
                            'Str To UTF-8',
                            'Base64 Eecode',
                            'Base64 Decode']

        self._decodeTypeFunc = [self.convertToChinese,
                                self.strToUnicode,
                                self.strToUtf8,
                                self.base64Encode,
                                self.base64Decode]

        # GUI components
        self._jLabelInput = swing.JLabel()
        self._jLabelOutput = swing.JLabel()
        self._jLabelExample = swing.JLabel()
        self._jLabelOputFormat = swing.JLabel()
        self._jCheckBoxOutputFormat = swing.JCheckBox()
        self._jTextAreaInputData = swing.JTextArea()
        self._jTextAreaOutputData = swing.JTextArea()
        self._jScrollPaneIntput = swing.JScrollPane(self._jTextAreaInputData)
        self._jScrollPaneOutput = swing.JScrollPane(self._jTextAreaOutputData)

        self._jButtonDecoder = swing.JButton('Execute', actionPerformed=self.decode)
        self._jComboDecodeType = swing.JComboBox(self._decodeType, actionListener=self.change_decode)

        # Configure GUI
        self._jLabelInput.setText('Input:')
        self._jLabelOutput.setText('Output:')
        self._jLabelExample.setText('Example: ')
        self._jLabelOputFormat.setText(r'Replace % with \ ')
        self._jLabelExample.setFont(Font("Consolas", Font.PLAIN, 14))

        self._jDecoderPanel.add(self._jLabelInput)
        self._jDecoderPanel.add(self._jLabelOutput)

        self._jScrollPaneIntput.setVerticalScrollBarPolicy(swing.JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED)
        self._jScrollPaneOutput.setVerticalScrollBarPolicy(swing.JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED)
        self._jLabelExample.setText(self._decodeTypeFunc[0]())


        # Configure locations
        self._jLabelInput.setBounds(20, 15, self.LABEL_WIDTH, self.LABEL_HEIGHT)
        self._jLabelOutput.setBounds(20, 225, self.LABEL_WIDTH, self.LABEL_HEIGHT)
        self._jLabelExample.setBounds(20, 190, self.TEXTAREA_WIDTH, 30)
        self._jLabelOputFormat.setBounds(self.TEXTAREA_WIDTH + 80, 117, 150, 30)
        self._jCheckBoxOutputFormat.setBounds(self.TEXTAREA_WIDTH + 50, 120, 20, 20)
        self._jScrollPaneIntput.setBounds(20 ,40, self.TEXTAREA_WIDTH, self.TEXTAREA_HEIGHT)
        self._jScrollPaneOutput.setBounds(20, 250, self.TEXTAREA_WIDTH, self.TEXTAREA_HEIGHT)
        self._jButtonDecoder.setBounds(self.TEXTAREA_WIDTH + 50, 40, 150, 30)
        self._jComboDecodeType.setBounds(self.TEXTAREA_WIDTH + 50, 80, 150,30)
 
        self._jDecoderPanel.add(self._jLabelInput)
        self._jDecoderPanel.add(self._jLabelOutput)
        self._jDecoderPanel.add(self._jLabelExample)
        self._jDecoderPanel.add(self._jLabelOputFormat)
        self._jDecoderPanel.add(self._jCheckBoxOutputFormat)
        self._jDecoderPanel.add(self._jComboDecodeType)
        self._jDecoderPanel.add(self._jScrollPaneIntput)
        self._jDecoderPanel.add(self._jScrollPaneOutput)
        self._jDecoderPanel.add(self._jButtonDecoder)

        # Setup Tabs
        self._jConfigTab = swing.JTabbedPane()
        self._jConfigTab.addTab("Decoder", self._jDecoderPanel)
        callbacks.customizeUiComponent(self._jConfigTab)
        callbacks.addSuiteTab(self)
        callbacks.registerContextMenuFactory(self)

        return


    def getTabCaption(self):
        return 'MyDecoder'

    def getUiComponent(self):
        return self._jConfigTab


    def createMenuItems(self, invocation):
        menu = []

        # Message Viewer will show menu item if selected by the user
        ctx = invocation.getInvocationContext()
        start = invocation.getSelectionBounds()[0];
        end = invocation.getSelectionBounds()[1];
        messages = invocation.getSelectedMessages();
        if end > start:
            if (ctx == invocation.CONTEXT_MESSAGE_EDITOR_REQUEST or
                ctx == invocation.CONTEXT_MESSAGE_VIEWER_REQUEST):
                if end > start:
                    selected_content = self._helpers.bytesToString(messages[0].getRequest()[start: end])

            if (ctx == invocation.CONTEXT_MESSAGE_EDITOR_RESPONSE or
                ctx == invocation.CONTEXT_MESSAGE_VIEWER_RESPONSE):
                selected_content = self._helpers.bytesToString(messages[0].getResponse())[start: end]

            menu.append(swing.JMenuItem("Send to MyDecoder", None, actionPerformed=lambda x, msg=selected_content: self.sendToMyDecoder(msg)))
        return menu if menu else None

    def sendToMyDecoder(self, msg):
        self._jTextAreaInputData.setText(msg)
        parentTab = self._jConfigTab.getParent()
        thread1 = self.HighlightParentTab(parentTab, self._jConfigTab)
        thread1.start()


    class HighlightParentTab(threading.Thread):
        def __init__(self, parentTab, childComponent):
            threading.Thread.__init__(self)
            self.parentTab = parentTab
            self.childComponent = childComponent

        def run(self):
            for i in range(self.parentTab.getTabCount()):
                if self.parentTab.getComponentAt(i).equals(self.childComponent):
                    self.parentTab.setBackgroundAt(i, Color(0xE58900))
                    time.sleep(3)
                    self.parentTab.setBackgroundAt(i, Color.BLACK)


    def decode(self, button):
        decodeType = self._jComboDecodeType.getSelectedIndex()
        data = self._decodeTypeFunc[decodeType](self._jTextAreaInputData.getText())

        self._jTextAreaOutputData.setText(data)


    def change_decode(self, button):
        decodeType = self._jComboDecodeType.getSelectedIndex()
        data = self._decodeTypeFunc[decodeType]()

        self._jLabelExample.setText(data)

    def convertToChinese(self, data=None):
        # convert %u6E2C%u8A66 or \u6E2C\u8A66 or %E4%B8%AD or \xE4\xB8\xAD to chinese
        if data is None:
            return r'Example: %u4E2D or \u4E2D to string'

        # Format \uXXXX
        re_unicode = re.findall(r'\\u([0-9a-zA-Z]{4})', data)
        for i in re_unicode:
            data = data.replace('\\u%s' %i, unichr(int(i, 16)))

        # Format %uXXXX
        re_unicode = re.findall(r'%u([0-9a-zA-Z]{4})', data)
        for i in re_unicode:
            data = data.replace(r'%u' + i, unichr(int(i, 16)))

        # Format %E4%B8%AD
        re_utf8 = re.findall('(%[\w]{2}%[\w]{2}%[\w]{2})', data)
        for i in re_utf8:
            data = data.replace(i, self.utf8ToStr(i))

        # Format \xE4\xB8\xAD 
        re_utf8 = re.findall(r'(\\x[\w]{2}\\x[\w]{2}\\x[\w]{2})', data)
        for i in re_utf8:
            data = data.replace(i, self.utf8ToStr(i))
        return data

    def utf8ToStr(self, data=None):
        # convert %E4%B8%AD to '中'
        if data is None:
            return r'Example: %e4%b8%ad or \xe4\xb8\xad to string'

        split_chr = '%'
        if re.search(r'^\\x.*', data) is not None:
            split_chr = r'\x'
        try:
            byte = ''.join(data.split(split_chr)[1:])
            byte = byte.decode("hex")
            return byte.decode('utf-8')
        except TypeError as e:
            print e
            return 'Error'


    def strToUnicode(self, data=None):
        if data is None:
            return r'Example: String to %u6E2C%u8A66 format'
        ret = ''
        if self._jCheckBoxOutputFormat.isSelected():
            ret = repr(data)[1:].replace("'", '')
        else:
            ret = repr(data)[1:].replace("'", '').replace(r'\u', '%u')

        return ret


    def strToUtf8(self, data=None):
        if data is None:
            return r'Example: String to %e4%b8%ad format'
        ret = ''
        if self._jCheckBoxOutputFormat.isSelected():
            ret = repr(data)[1:].replace("'", '').replace(r'\x', '%')
        else:
            ret = repr(data)[1:].replace("'", '')

        return ret


    def base64Decode(self, data=None):
        if data is None:
            return r'Base64 Decoder'

        return base64.b64decode(data).decode('utf-8')


    def base64Encode(self, data=None):
        if data is None:
            return r'Base64 Encoder'

        return base64.b64encode(data.encode('utf-8'))
