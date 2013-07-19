#!/usr/bin/env python
# header.py - Generate C++ header files from IDL.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys, os, xpidl, makeutils

def strip_end(text, suffix):
    if not text.endswith(suffix):
        return text
    return text[:-len(suffix)]

def findIDL(includePath, interfaceFileName):
    for d in includePath:
        # Not os.path.join: we need a forward slash even on Windows because
        # this filename ends up in makedepend output.
        path = d + '/' + interfaceFileName
        if os.path.exists(path):
            return path
    raise BaseException("No IDL file found for interface %s "
                        "in include path %r"
                        % (interfaceFileName, includePath))

def loadIDL(parser, includePath, filename):
    idlFile = findIDL(includePath, filename)
    if not idlFile in makeutils.dependencies:
        makeutils.dependencies.append(idlFile)
    idl = p.parse(open(idlFile).read(), idlFile)
    idl.resolve(includePath, p)
    return idl

def loadEventIDL(parser, includePath, eventname):
    eventidl = ("nsIDOM%s.idl" % eventname)
    idlFile = findIDL(includePath, eventidl)
    if not idlFile in makeutils.dependencies:
        makeutils.dependencies.append(idlFile)
    idl = p.parse(open(idlFile).read(), idlFile)
    idl.resolve(includePath, p)
    return idl

class Configuration:
    def __init__(self, filename):
        config = {}
        execfile(filename, config)
        self.simple_events = config.get('simple_events', [])
        self.special_includes = config.get('special_includes', [])
        self.exclude_automatic_type_include = config.get('exclude_automatic_type_include', [])

def readConfigFile(filename):
    return Configuration(filename)

def firstCap(str):
    return str[0].upper() + str[1:]

def print_header_file(fd, conf):
    fd.write("#if defined MOZ_GENERATED_EVENT_LIST\n")
    for e in conf.simple_events:
        fd.write("MOZ_GENERATED_EVENT(%s)\n" % e);
    fd.write("#undef MOZ_GENERATED_EVENT\n");
    fd.write("\n#elif defined MOZ_GENERATED_EVENTS_INCLUDES\n")
    for e in conf.simple_events:
        fd.write("#include \"nsIDOM%s.h\"\n" % e)
    fd.write("#else\n")
    fd.write("#ifndef _gen_mozilla_idl_generated_events_h_\n"
             "#define _gen_mozilla_idl_generated_events_h_\n\n")
    fd.write("/* THIS FILE IS AUTOGENERATED - DO NOT EDIT */\n")
    fd.write("#include \"nscore.h\"\n")
    fd.write("class nsEvent;\n")
    fd.write("class nsIDOMEvent;\n")
    fd.write("class nsPresContext;\n")
    fd.write("namespace mozilla {\n");
    fd.write("namespace dom {\n");
    fd.write("class EventTarget;\n")
    fd.write("}\n");
    fd.write("}\n\n");
    for e in conf.simple_events:
        fd.write("nsresult\n")
        fd.write("NS_NewDOM%s(nsIDOMEvent** aInstance, " % e)
        fd.write("mozilla::dom::EventTarget* aOwner, ")
        fd.write("nsPresContext* aPresContext, nsEvent* aEvent);\n")
 
    fd.write("\n#endif\n")
    fd.write("#endif\n")

def collect_names_and_non_primitive_attribute_types(idl, attrnames, forwards):
    for p in idl.productions:
        if p.kind == 'interface' or p.kind == 'dictionary':
            interfaces = []
            base = p.base
            baseiface = p
            while base is not None:
                baseiface = baseiface.idl.getName(baseiface.base, baseiface.location)    
                interfaces.append(baseiface)
                base = baseiface.base

            interfaces.reverse()
            interfaces.append(p)

            for iface in interfaces:
                collect_names_and_non_primitive_attribute_types_from_interface(iface, attrnames, forwards)

def collect_names_and_non_primitive_attribute_types_from_interface(iface, attrnames, forwards):
    for member in iface.members:
        if isinstance(member, xpidl.Attribute):
            if not member.name in attrnames:
                attrnames.append(member.name)
            if member.realtype.nativeType('in').endswith('*'):
                t = member.realtype.nativeType('in').strip('* ')
                if not t in forwards:
                    forwards.append(t)

def print_cpp(idl, fd, conf, eventname):
    for p in idl.productions:
        if p.kind == 'interface':
            write_cpp(eventname, p, fd)

def print_cpp_file(fd, conf):
    fd.write("/* THIS FILE IS AUTOGENERATED - DO NOT EDIT */\n\n")
    fd.write('#include "GeneratedEvents.h"\n')
    fd.write('#include "nsDOMClassInfoID.h"\n')
    fd.write('#include "nsPresContext.h"\n')
    fd.write('#include "nsGUIEvent.h"\n')
    fd.write('#include "nsDOMEvent.h"\n');
    fd.write('#include "mozilla/dom/EventTarget.h"\n');

    includes = []
    for s in conf.special_includes:
        if not s in includes:
            includes.append(strip_end(s, ".h"))
    
    for e in conf.simple_events:
        if not e in includes:
            includes.append(("nsIDOM%s" % e))

    attrnames = []
    for e in conf.simple_events:
        idl = loadEventIDL(p, options.incdirs, e)
        collect_names_and_non_primitive_attribute_types(idl, attrnames, includes)
    
    for c in includes:
      if not c in conf.exclude_automatic_type_include:
            fd.write("#include \"%s.h\"\n" % c)

    for e in conf.simple_events:
        idlname = ("nsIDOM%s.idl" % e)
        idl = p.parse(open(findIDL(options.incdirs, idlname)).read(), idlname)
        idl.resolve(options.incdirs, p)
        print_cpp(idl, fd, conf, e)

def init_value(attribute):
    realtype = attribute.realtype.nativeType('in')
    realtype = realtype.strip(' ')
    if realtype.endswith('*'):
        return "nullptr"
    if realtype == "bool":
        return "false"
    if realtype.count("nsAString"):
        return ""
    if realtype.count("nsACString"):
        return ""
    if realtype.count("JS::Value"):
      raise BaseException("JS::Value not supported in simple events!")
    return "0"

def attributeVariableTypeAndName(a):
    if a.realtype.nativeType('in').endswith('*'):
        l = ["nsCOMPtr<%s> m%s;" % (a.realtype.nativeType('in').strip('* '),
                   firstCap(a.name))]
    elif a.realtype.nativeType('in').count("nsAString"):
        l = ["nsString m%s;" % firstCap(a.name)]
    elif a.realtype.nativeType('in').count("nsACString"):
        l = ["nsCString m%s;" % firstCap(a.name)]
    else:
        l = ["%sm%s;" % (a.realtype.nativeType('in'),
                       firstCap(a.name))]
    return ", ".join(l)

def writeAttributeGetter(fd, classname, a):
    fd.write("NS_IMETHODIMP\n")
    fd.write("%s::Get%s(" % (classname, firstCap(a.name)))
    if a.realtype.nativeType('in').endswith('*'):
        fd.write("%s** a%s" % (a.realtype.nativeType('in').strip('* '), firstCap(a.name)))
    elif a.realtype.nativeType('in').count("nsAString"):
        fd.write("nsAString& a%s" % firstCap(a.name))
    elif a.realtype.nativeType('in').count("nsACString"):
        fd.write("nsACString& a%s" % firstCap(a.name))
    else:
        fd.write("%s*a%s" % (a.realtype.nativeType('in'), firstCap(a.name)))
    fd.write(")\n");
    fd.write("{\n");
    if a.realtype.nativeType('in').endswith('*'):
        fd.write("  NS_IF_ADDREF(*a%s = m%s);\n" % (firstCap(a.name), firstCap(a.name)))
    elif a.realtype.nativeType('in').count("nsAString"):
        fd.write("  a%s = m%s;\n" % (firstCap(a.name), firstCap(a.name)))
    elif a.realtype.nativeType('in').count("nsACString"):
        fd.write("  a%s = m%s;\n" % (firstCap(a.name), firstCap(a.name)))
    else:
        fd.write("  *a%s = m%s;\n" % (firstCap(a.name), firstCap(a.name)))
    fd.write("  return NS_OK;\n");
    fd.write("}\n\n");

def writeAttributeParams(fd, a):
    if a.realtype.nativeType('in').endswith('*'):
        fd.write(", %s* a%s" % (a.realtype.nativeType('in').strip('* '), firstCap(a.name)))
    elif a.realtype.nativeType('in').count("nsAString"):
        fd.write(", const nsAString& a%s" % firstCap(a.name))
    elif a.realtype.nativeType('in').count("nsACString"):
        fd.write(", const nsACString& a%s" % firstCap(a.name))
    else:
        fd.write(", %s a%s" % (a.realtype.nativeType('in'), firstCap(a.name)))

def write_cpp(eventname, iface, fd):
    classname = ("nsDOM%s" % eventname)
    basename = ("ns%s" % iface.base[3:])
    attributes = []
    ccattributes = []
    for member in iface.members:
        if isinstance(member, xpidl.Attribute):
            attributes.append(member)
            if (member.realtype.nativeType('in').endswith('*')):
                ccattributes.append(member);

    baseinterfaces = []
    baseiface = iface.idl.getName(iface.base, iface.location)
    while baseiface.name != "nsIDOMEvent":
        baseinterfaces.append(baseiface)
        baseiface = baseiface.idl.getName(baseiface.base, baseiface.location)
    baseinterfaces.reverse()

    baseattributes = []
    for baseiface in baseinterfaces:
        for member in baseiface.members:
            if isinstance(member, xpidl.Attribute):
                baseattributes.append(member)


    fd.write("\nclass %s : public %s, public %s\n" % (classname, basename, iface.name))
    fd.write("{\n")
    fd.write("public:\n")
    fd.write("  %s(mozilla::dom::EventTarget* aOwner, " % classname)
    fd.write("nsPresContext* aPresContext = nullptr, nsEvent* aEvent = nullptr)\n");
    fd.write("  : %s(aOwner, aPresContext, aEvent)" % basename)
    for a in attributes:
        fd.write(",\n    m%s(%s)" % (firstCap(a.name), init_value(a)))
    fd.write("\n  {}\n")
    fd.write("  virtual ~%s() {}\n\n" % classname)
    fd.write("  NS_DECL_ISUPPORTS_INHERITED\n")
    fd.write("  NS_DECL_CYCLE_COLLECTION_CLASS_INHERITED(%s, %s)\n" % (classname, basename))
    fd.write("  NS_FORWARD_TO_NSDOMEVENT\n")

    for baseiface in baseinterfaces:
        baseimpl = ("ns%s" % baseiface.name[3:])
        fd.write("  NS_FORWARD_%s(%s::)\n" % (baseiface.name.upper(), baseimpl))

    fd.write("  NS_DECL_%s\n" % iface.name.upper())
    fd.write("  virtual nsresult InitFromCtor(const nsAString& aType, JSContext* aCx, jsval* aVal);\n")
    fd.write("protected:\n")
    for a in attributes:
        fd.write("  %s\n" % attributeVariableTypeAndName(a))
    fd.write("};\n\n")

    fd.write("NS_IMPL_CYCLE_COLLECTION_UNLINK_BEGIN_INHERITED(%s, %s)\n" % (classname, basename))
    for c in ccattributes:
        fd.write("  NS_IMPL_CYCLE_COLLECTION_UNLINK(m%s)\n" % firstCap(c.name))
    fd.write("NS_IMPL_CYCLE_COLLECTION_UNLINK_END\n\n");
    fd.write("NS_IMPL_CYCLE_COLLECTION_TRAVERSE_BEGIN_INHERITED(%s, %s)\n" % (classname, basename))
    for c in ccattributes:
        fd.write("  NS_IMPL_CYCLE_COLLECTION_TRAVERSE(m%s)\n" % firstCap(c.name))
    fd.write("NS_IMPL_CYCLE_COLLECTION_TRAVERSE_END\n\n");

    fd.write("NS_IMPL_ADDREF_INHERITED(%s, %s)\n" % (classname, basename))
    fd.write("NS_IMPL_RELEASE_INHERITED(%s, %s)\n\n" % (classname, basename))

    fd.write("DOMCI_DATA(%s, %s)\n\n" % (eventname, classname))

    fd.write("NS_INTERFACE_MAP_BEGIN_CYCLE_COLLECTION_INHERITED(%s)\n" % classname)
    fd.write("  NS_INTERFACE_MAP_ENTRY(nsIDOM%s)\n" % eventname)
    fd.write("  NS_DOM_INTERFACE_MAP_ENTRY_CLASSINFO(%s)\n" % eventname)
    fd.write("NS_INTERFACE_MAP_END_INHERITING(%s)\n\n" % basename)

    fd.write("nsresult\n")
    fd.write("%s::InitFromCtor(const nsAString& aType, JSContext* aCx, jsval* aVal)\n" % classname)
    fd.write("{\n");
    fd.write("  mozilla::idl::%sInit d;\n" % eventname)
    fd.write("  nsresult rv = d.Init(aCx, aVal);\n")
    fd.write("  NS_ENSURE_SUCCESS(rv, rv);\n")
    fd.write("  return Init%s(aType, d.bubbles, d.cancelable" % eventname)
    for a in baseattributes:
      fd.write(", d.%s" % a.name)
    for a in attributes:
        fd.write(", d.%s" % a.name)
    fd.write(");\n")
    fd.write("}\n\n")

    fd.write("NS_IMETHODIMP\n")
    fd.write("%s::Init%s(" % (classname, eventname))
    fd.write("const nsAString& aType, bool aCanBubble, bool aCancelable")
    for a in baseattributes:
      writeAttributeParams(fd, a)
    for a in attributes:
        writeAttributeParams(fd, a)
    fd.write(")\n{\n")
    fd.write("  nsresult rv = %s::Init%s(aType, aCanBubble, aCancelable" % (basename, basename[5:]))
    for a in baseattributes:
      fd.write(", a%s" % firstCap(a.name))
    fd.write(");\n");
    fd.write("  NS_ENSURE_SUCCESS(rv, rv);\n")
    for a in attributes:
        fd.write("  m%s = a%s;\n" % (firstCap(a.name), firstCap(a.name)))
    fd.write("  return NS_OK;\n")
    fd.write("}\n\n")

    for a in attributes:
        writeAttributeGetter(fd, classname, a)

    fd.write("nsresult\n")
    fd.write("NS_NewDOM%s(nsIDOMEvent** aInstance, "  % eventname)
    fd.write("mozilla::dom::EventTarget* aOwner, nsPresContext* aPresContext = nullptr, nsEvent* aEvent = nullptr)\n")
    fd.write("{\n")
    fd.write("  %s* it = new %s(aOwner, aPresContext, aEvent);\n" % (classname, classname))
    fd.write("  return CallQueryInterface(it, aInstance);\n")
    fd.write("}\n\n")

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser(usage="usage: %prog [options] configfile")
    o.add_option('-I', action='append', dest='incdirs', default=['.'],
                 help="Directory to search for imported files")
    o.add_option('-o', "--stub-output",
                 type='string', dest='stub_output', default=None,
                 help="Quick stub C++ source output file", metavar="FILE")
    o.add_option('--header-output', type='string', default=None,
                 help="Quick stub header output file", metavar="FILE")
    o.add_option('--makedepend-output', type='string', default=None,
                 help="gnumake dependencies output file", metavar="FILE")
    o.add_option('--cachedir', dest='cachedir', default=None,
                 help="Directory in which to cache lex/parse tables.")
    (options, filenames) = o.parse_args()
    if len(filenames) != 1:
        o.error("Exactly one config filename is needed.")
    filename = filenames[0]

    if options.cachedir is not None:
        if not os.path.isdir(options.cachedir):
            os.mkdir(options.cachedir)
        sys.path.append(options.cachedir)

    # Instantiate the parser.
    p = xpidl.IDLParser(outputdir=options.cachedir)

    conf = readConfigFile(filename)

    if options.stub_output is not None:
        makeutils.targets.append(options.stub_output)
        outfd = open(options.stub_output, 'w')
        print_cpp_file(outfd, conf)
        outfd.close()
        if options.makedepend_output is not None:
            makeutils.writeMakeDependOutput(options.makedepend_output)
    if options.header_output is not None:
        outfd = open(options.header_output, 'w')
        print_header_file(outfd, conf)
        outfd.close()

