import os
import sys
import glob
import string

import yaml
import jsonschema
import munch

THIS_SCRIPT_DIR      = os.path.dirname( os.path.abspath( __file__ ) )
TEMPLATE_DIR         = os.path.join( THIS_SCRIPT_DIR, 'templates' )
DEFAULT_OUTPUT_DIR   = 'out'
SCHEMA_FILE          = os.path.join( THIS_SCRIPT_DIR, 'schema.yaml' )
TEMPLATE_SCHEMA_FILE = os.path.join( THIS_SCRIPT_DIR, 'template_schema.yaml' )

def create_munch( dictionary, none_altanative = '' ):
    result = munch.DefaultMunch( '', dictionary )
    for k in dictionary.keys():
        if result[ k ] is None:
            result[ k ] = none_altanative

    return result

def validate_yaml( source, schema ):
    try:
        jsonschema.validate( source, schema )
    except Exception:
        raise Exception( 'Yaml Validation Failed!' )

def load_text( filename, encoding = 'utf8' ):
    with open( filename, mode = 'r', encoding = encoding ) as fp:
        return fp.read()

def load_yaml( filename ) :
    return create_munch( yaml.safe_load( load_text( filename ) ) )

def load_template( filename ):
    return string.Template( load_text( filename ) )

def generate_code( template, parameter_dict = {} ):
    return template.safe_substitute( parameter_dict )

def generate_fully_classname( class_info, template_info ):
    return "{name_prefix}{name}{name_suffix}".format(
            name_prefix = template_info.prefix,
            name        = class_info.name,
            name_suffix = template_info.suffix
    )

def process_output( code_text, config_data, class_info, template_meta ):

    template_info = config_data.template_table[ template_meta.name ]

    output_filename = "{name}{suffix}".format(
        name        = generate_fully_classname( class_info, template_info ),
        suffix      = config_data.suffix
    )

    output_dir = DEFAULT_OUTPUT_DIR
    if 'output_dir' in template_meta:
        output_dir = template_meta.output_dir
    if 'output_dir' in config_data:
        output_dir = config_data.output_dir

    output_path = os.path.join( output_dir, output_filename )

    print( "--> " + output_path )

    os.makedirs( output_dir, exist_ok = True )

    with open( output_path, 'w', encoding='utf8' ) as fp:
        fp.write( code_text )

def generate_replace_variables( config_data, class_info, template_info ):
    values = create_munch( {} )
    values.classname    = generate_fully_classname( class_info, template_info )
    values.prefix       = template_info.prefix
    values.suffix       = template_info.suffix
    values.name         = class_info.name
    values.description  = class_info.description

    if len( class_info.namespace ) > 0 :
        class_info.namespace = class_info.namespace
    else:
        values.namespace = config_data.namespace

    if type( class_info.user_variables ) is dict:
        values.update( class_info.user_variables )

    return values

def process_template( config_data, class_info, template_meta ):

    if not template_meta.name in config_data.template_table:
        print( "template: `{name}` is not found.".format( name = template_meta.name ) )
        return

    template_info = config_data.template_table[ template_meta.name ]
    template_text = load_template( os.path.join( TEMPLATE_DIR, template_info.path ) )

    values = generate_replace_variables( config_data, class_info, template_info )
    # print( values )

    code_text = generate_code( template_text, values )
    process_output( code_text, config_data, class_info, template_meta )

def process_class( config_data, class_info ):
    print( class_info.name )
    for x in class_info.templates:
        process_template( config_data, class_info, create_munch( x ) )

def main( argv ):
    for input_file in argv:
        print( input_file )

        schema_data = load_yaml( SCHEMA_FILE )
        config_data = load_yaml( input_file )
        validate_yaml( config_data, schema_data )

        template_table  = create_munch( {} )
        template_schema = load_yaml( TEMPLATE_SCHEMA_FILE )
        for x in glob.glob( os.path.join( TEMPLATE_DIR, '**', '*.yaml' ) ):
            template_info = load_yaml( x )
            validate_yaml( template_info, template_schema )

            template_table[ template_info.name ] = template_info

        config_data.template_table = template_table

        for x in config_data.classes:
            process_class( config_data, create_munch( x ) )

if __name__ == '__main__':
    if len( sys.argv ) > 1:
        main( sys.argv[ 1: ] )